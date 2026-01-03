"""
Django management command to start the real-time log listener.

This command:
1. Starts the Redis Pub/Sub listener for Logstash logs
2. Starts the metrics broadcast loop
3. Runs until interrupted (Ctrl+C)

Usage:
    python manage.py start_realtime_listener
    
Run as a separate Docker service for production.
"""

import asyncio
import signal
import sys
from django.core.management.base import BaseCommand

from api.realtime import RedisPubSubBridge, broadcast_metrics_loop


class Command(BaseCommand):
    help = 'Start the real-time log listener (Redis Pub/Sub to WebSocket bridge)'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bridge = None
        self._loop = None
        self._tasks = []
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--metrics-interval',
            type=float,
            default=1.0,
            help='Interval in seconds for broadcasting metrics (default: 1.0)',
        )
        parser.add_argument(
            '--no-metrics',
            action='store_true',
            help='Disable metrics broadcasting',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting real-time log listener...'))
        
        # Set up asyncio event loop
        if sys.platform == 'win32':
            # Windows requires ProactorEventLoop for subprocess support
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        try:
            self._loop.run_until_complete(self._run(options))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nReceived interrupt, shutting down...'))
        finally:
            self._cleanup()
            self._loop.close()
            self.stdout.write(self.style.SUCCESS('Real-time listener stopped.'))
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        try:
            self._loop.add_signal_handler(
                signal.SIGINT, 
                lambda: self._loop.create_task(self._shutdown())
            )
            self._loop.add_signal_handler(
                signal.SIGTERM, 
                lambda: self._loop.create_task(self._shutdown())
            )
        except NotImplementedError:
            # Signal handlers not supported on Windows
            pass
    
    async def _run(self, options):
        """Main async run loop."""
        self._bridge = RedisPubSubBridge()
        
        # Start the Redis listener task
        redis_task = asyncio.create_task(
            self._bridge.run(),
            name='redis_listener'
        )
        self._tasks.append(redis_task)
        self.stdout.write(self.style.SUCCESS('Redis Pub/Sub listener started.'))
        
        # Start the metrics broadcast task (unless disabled)
        if not options.get('no_metrics'):
            metrics_interval = options.get('metrics_interval', 1.0)
            metrics_task = asyncio.create_task(
                broadcast_metrics_loop(interval_seconds=metrics_interval),
                name='metrics_broadcast'
            )
            self._tasks.append(metrics_task)
            self.stdout.write(self.style.SUCCESS(
                f'Metrics broadcast started (interval: {metrics_interval}s).'
            ))
        
        self.stdout.write(self.style.SUCCESS(
            'Real-time listener running. Press Ctrl+C to stop.'
        ))
        
        # Wait for all tasks
        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            pass
    
    async def _shutdown(self):
        """Graceful shutdown."""
        self.stdout.write(self.style.WARNING('Shutting down gracefully...'))
        
        # Stop the bridge
        if self._bridge:
            self._bridge.stop()
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    def _cleanup(self):
        """Cleanup resources."""
        # Cancel any remaining tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # Run pending callbacks
        self._loop.run_until_complete(asyncio.sleep(0.1))
