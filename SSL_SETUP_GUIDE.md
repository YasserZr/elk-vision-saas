# SSL/HTTPS Setup Guide

Complete guide for securing your ELK Vision SaaS application with HTTPS and proper CORS configuration.

## Table of Contents
- [Prerequisites](#prerequisites)
- [SSL Certificate Options](#ssl-certificate-options)
- [Let's Encrypt Setup (Recommended)](#lets-encrypt-setup-recommended)
- [Custom SSL Certificates](#custom-ssl-certificates)
- [NGINX Configuration](#nginx-configuration)
- [CORS Configuration](#cors-configuration)
- [Testing SSL Setup](#testing-ssl-setup)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before setting up SSL, ensure you have:
- A registered domain name pointing to your server's IP address
- DNS A records configured for your domain
- Ports 80 and 443 open in your firewall
- Docker and Docker Compose installed

---

## SSL Certificate Options

### 1. Let's Encrypt (Free, Recommended)
- Free SSL certificates
- Auto-renewal available
- Trusted by all major browsers
- Rate limits: 50 certificates per domain per week

### 2. Commercial SSL Certificates
- Purchase from providers like DigiCert, Sectigo, GlobalSign
- Extended Validation (EV) certificates available
- Wildcard certificates for subdomains
- Higher warranty and support

### 3. Self-Signed Certificates (Development Only)
- Free but not trusted by browsers
- Only use for local development
- Will show security warnings

---

## Let's Encrypt Setup (Recommended)

### Step 1: Update docker-compose.yml

Add certbot service to your `docker-compose.yml`:

```yaml
services:
  # ... existing services ...

  certbot:
    image: certbot/certbot:latest
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - frontend_network
```

Update nginx service volumes:

```yaml
  nginx:
    # ... existing config ...
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
      - static_files:/var/www/static:ro
      - media_files:/var/www/media:ro
```

### Step 2: Initial Certificate Generation

Create directories:
```powershell
New-Item -ItemType Directory -Force -Path certbot\conf, certbot\www
```

Start nginx temporarily for certificate validation:
```powershell
docker-compose up -d nginx
```

Request certificate (replace with your domain):
```powershell
docker-compose run --rm certbot certonly --webroot `
  --webroot-path=/var/www/certbot `
  --email your-email@example.com `
  --agree-tos `
  --no-eff-email `
  -d yourdomain.com `
  -d www.yourdomain.com
```

### Step 3: Update NGINX Configuration

Edit `nginx/conf.d/default.conf`:

1. Replace `yourdomain.com` with your actual domain in all locations
2. Ensure the HTTPS server block is uncommented (already done in the provided config)
3. Update CORS origin to match your frontend domain

### Step 4: Restart Services

```powershell
docker-compose restart nginx
docker-compose up -d certbot
```

### Step 5: Test Auto-Renewal

```powershell
docker-compose run --rm certbot renew --dry-run
```

---

## Custom SSL Certificates

If you have purchased SSL certificates:

### Step 1: Prepare Certificate Files

Place your certificate files in the appropriate directory:
```
nginx/
  ssl/
    yourdomain.com.crt      # Your SSL certificate
    yourdomain.com.key      # Private key
    ca-bundle.crt           # CA bundle (if provided)
```

### Step 2: Update NGINX Configuration

Edit the HTTPS server block in `nginx/conf.d/default.conf`:

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # Custom SSL certificates
    ssl_certificate /etc/nginx/ssl/yourdomain.com.crt;
    ssl_certificate_key /etc/nginx/ssl/yourdomain.com.key;
    ssl_trusted_certificate /etc/nginx/ssl/ca-bundle.crt;

    # ... rest of configuration ...
}
```

### Step 3: Update docker-compose.yml

Mount SSL directory:
```yaml
  nginx:
    volumes:
      - ./nginx/ssl:/etc/nginx/ssl:ro
      # ... other volumes ...
```

---

## Self-Signed Certificates (Development Only)

### Generate Self-Signed Certificate

```powershell
# Create SSL directory
New-Item -ItemType Directory -Force -Path nginx\ssl

# Generate certificate (requires OpenSSL)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout nginx\ssl\selfsigned.key `
  -out nginx\ssl\selfsigned.crt `
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### Update NGINX for Self-Signed

```nginx
server {
    listen 443 ssl http2;
    server_name localhost;

    ssl_certificate /etc/nginx/ssl/selfsigned.crt;
    ssl_certificate_key /etc/nginx/ssl/selfsigned.key;

    # ... rest of configuration ...
}
```

---

## NGINX Configuration

### Current Setup

The provided NGINX configuration includes:

1. **Three Server Blocks:**
   - HTTP (port 80): Redirects to HTTPS + Let's Encrypt ACME challenge
   - HTTPS (port 443): Production with SSL and strict CORS
   - Development (port 8080): Local testing without SSL, permissive CORS

2. **Security Headers:**
   - HSTS (Strict-Transport-Security)
   - X-Frame-Options
   - X-Content-Type-Options
   - X-XSS-Protection
   - Referrer-Policy
   - Permissions-Policy

3. **Rate Limiting:**
   - API: 10 requests/second with 20 burst
   - General: 50 requests/second with 100 burst

4. **SSL Configuration:**
   - TLS 1.2 and 1.3 only
   - Modern cipher suites
   - OCSP stapling
   - Session caching

### Customize for Your Domain

Edit `nginx/conf.d/default.conf` and replace:
- `yourdomain.com` with your actual domain
- Update CORS allowed origins in the CORS section
- Adjust rate limits if needed

---

## CORS Configuration

### Understanding CORS in the Config

The NGINX configuration implements CORS for:
- API endpoints (`/api/`)
- WebSocket connections (`/ws/`)
- Static and media files

### Allowed Origins

By default, CORS allows:
- `https://yourdomain.com`
- `https://www.yourdomain.com`
- `http://localhost:3000` (development)

### Customize CORS Origins

Edit the CORS section in `nginx/conf.d/default.conf`:

```nginx
# CORS headers for API requests
set $cors_origin "";
set $cors_cred "true";
set $cors_methods "GET, POST, PUT, DELETE, PATCH, OPTIONS";
set $cors_headers "Authorization, Content-Type, Accept, Origin, X-Requested-With";

# Allow your domains (use regex)
if ($http_origin ~* (https://yourdomain\.com|https://www\.yourdomain\.com|https://app\.yourdomain\.com|http://localhost:3000)) {
    set $cors_origin $http_origin;
}
```

### Add Multiple Subdomains

To allow multiple subdomains:

```nginx
if ($http_origin ~* (https://([a-z0-9-]+\.)?yourdomain\.com|http://localhost:3000)) {
    set $cors_origin $http_origin;
}
```

### CORS for WebSocket

WebSocket CORS is configured in the `/ws/` location:

```nginx
location /ws/ {
    # CORS for WebSocket
    if ($cors_origin != "") {
        add_header 'Access-Control-Allow-Origin' $cors_origin always;
        add_header 'Access-Control-Allow-Credentials' $cors_cred always;
    }
    # ... rest of config ...
}
```

### Disable CORS (Not Recommended)

To allow all origins (development only):

```nginx
set $cors_origin "*";
set $cors_cred "false";  # Must be false with wildcard
```

---

## Testing SSL Setup

### 1. Basic HTTPS Test

```powershell
# Test HTTPS connection
curl -I https://yourdomain.com

# Expected: HTTP/2 200
```

### 2. SSL Certificate Validation

```powershell
# Check certificate details
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### 3. SSL Labs Test

Visit: https://www.ssllabs.com/ssltest/

Enter your domain and run a full test. Aim for an A+ rating.

### 4. Test CORS

```powershell
# Test CORS preflight
curl -X OPTIONS https://yourdomain.com/api/logs/ `
  -H "Origin: https://yourdomain.com" `
  -H "Access-Control-Request-Method: POST" `
  -H "Access-Control-Request-Headers: Authorization, Content-Type" `
  -v
```

Expected headers:
```
Access-Control-Allow-Origin: https://yourdomain.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
```

### 5. Test HTTP to HTTPS Redirect

```powershell
curl -I http://yourdomain.com
# Expected: 301 Moved Permanently
# Location: https://yourdomain.com/
```

### 6. Test WebSocket over SSL

```javascript
// In browser console on https://yourdomain.com
const ws = new WebSocket('wss://yourdomain.com/ws/notifications/?token=YOUR_JWT');
ws.onopen = () => console.log('Connected!');
ws.onerror = (e) => console.error('Error:', e);
```

---

## Troubleshooting

### Certificate Not Loading

**Symptom:** NGINX fails to start with SSL error

**Solutions:**
1. Check certificate paths in NGINX config:
   ```powershell
   docker-compose exec nginx ls -la /etc/letsencrypt/live/yourdomain.com/
   ```

2. Verify certificate permissions:
   ```powershell
   docker-compose exec nginx nginx -t
   ```

3. Check NGINX error logs:
   ```powershell
   docker-compose logs nginx
   ```

### CORS Not Working

**Symptom:** Browser shows CORS errors

**Solutions:**
1. Verify origin in NGINX config matches exactly (including protocol and port)
2. Check that preflight OPTIONS requests return 204:
   ```powershell
   curl -X OPTIONS https://yourdomain.com/api/logs/ -I
   ```
3. Ensure credentials are set correctly (`true` with specific origins, `false` with `*`)

### Let's Encrypt Rate Limit

**Symptom:** Certificate request fails with rate limit error

**Solutions:**
1. Use staging environment for testing:
   ```powershell
   docker-compose run --rm certbot certonly --webroot `
     --webroot-path=/var/www/certbot `
     --staging `
     -d yourdomain.com
   ```

2. Wait for rate limit to reset (weekly)
3. Use DNS validation instead of HTTP validation

### Mixed Content Warnings

**Symptom:** Browser console shows "Mixed Content" warnings

**Solutions:**
1. Ensure all API calls use HTTPS:
   ```typescript
   const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://yourdomain.com/api';
   ```

2. Update frontend environment variables:
   ```bash
   NEXT_PUBLIC_API_URL=https://yourdomain.com/api
   NEXT_PUBLIC_WS_URL=wss://yourdomain.com/ws
   ```

3. Check for hardcoded HTTP URLs in code

### WebSocket Connection Fails

**Symptom:** WebSocket connection drops or fails to connect

**Solutions:**
1. Verify WebSocket upgrade headers:
   ```powershell
   docker-compose exec nginx cat /etc/nginx/conf.d/default.conf | Select-String -Pattern "Upgrade"
   ```

2. Check WebSocket URL uses `wss://` not `ws://`
3. Increase timeout values in NGINX:
   ```nginx
   proxy_read_timeout 7200s;  # 2 hours
   proxy_send_timeout 7200s;
   ```

### Certificate Renewal Fails

**Symptom:** Auto-renewal doesn't work

**Solutions:**
1. Test renewal manually:
   ```powershell
   docker-compose run --rm certbot renew --dry-run
   ```

2. Check certbot logs:
   ```powershell
   docker-compose logs certbot
   ```

3. Ensure `.well-known/acme-challenge/` is accessible:
   ```powershell
   curl http://yourdomain.com/.well-known/acme-challenge/test
   ```

---

## Production Checklist

Before going to production:

- [ ] Domain DNS A records point to server IP
- [ ] Firewall allows ports 80 and 443
- [ ] SSL certificates installed and valid
- [ ] NGINX config uses production domains
- [ ] CORS configured with specific origins (no wildcards)
- [ ] Rate limiting configured appropriately
- [ ] Security headers enabled
- [ ] HTTP redirects to HTTPS
- [ ] WebSocket connections work over WSS
- [ ] SSL test passes with A+ rating
- [ ] Certificate auto-renewal tested
- [ ] Monitoring and alerts configured
- [ ] Backup of SSL certificates exists

---

## Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [NGINX WebSocket Proxying](http://nginx.org/en/docs/http/websocket.html)
- [CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [SSL Labs Testing](https://www.ssllabs.com/ssltest/)

---

## Quick Reference

### Useful Commands

```powershell
# Generate Let's Encrypt certificate
docker-compose run --rm certbot certonly --webroot -w /var/www/certbot -d yourdomain.com

# Renew certificates
docker-compose run --rm certbot renew

# Test NGINX configuration
docker-compose exec nginx nginx -t

# Reload NGINX
docker-compose exec nginx nginx -s reload

# View certificate details
openssl x509 -in certbot/conf/live/yourdomain.com/cert.pem -text -noout

# Check certificate expiration
openssl x509 -in certbot/conf/live/yourdomain.com/cert.pem -noout -enddate

# Monitor NGINX access logs
docker-compose logs -f nginx

# Test HTTPS connection
curl -I https://yourdomain.com

# Test CORS
curl -H "Origin: https://yourdomain.com" https://yourdomain.com/api/health/ -I
```

### Port Reference

- **80**: HTTP (redirects to HTTPS)
- **443**: HTTPS with SSL
- **8080**: Development server (no SSL, permissive CORS)

### Environment Variables

Update these in `.env`:

```bash
# Domain configuration
DOMAIN=yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# SSL email for Let's Encrypt
SSL_EMAIL=admin@yourdomain.com

# Frontend URL (for CORS)
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXT_PUBLIC_WS_URL=wss://yourdomain.com/ws
```
