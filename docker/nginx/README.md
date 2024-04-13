# SSL Certificates For NGINX

By default NGINX come equipped with a self-digned SSL certificate which is generated upon image build.

## Generate a Self-Signed SSL Certificate for NGINX

You can generate a self-signed SSL certificate using OpenSSL. Here's a command to generate a self-signed certificate and key pair. Replace /path/to/server.key and /path/to/server.crt with the paths where you want to store your private key and certificate files, copy/paste line of code and you're done!

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /path/to/server.key -out /path/to/server.crt
```

### Configure NGINX to Use the Self-Signed Certificate

Check that your NGINX configuration configured to use self-signed SSL certificate:
```nginx configuration
server {
    listen 443 ssl;
    server_name your_domain.local;

    ssl_certificate /path/to/server.crt;
    ssl_certificate_key /path/to/server.key;

    # ...
}
```

[HOWTO Add Self-Signed Certificate to the Client (Web Browser)](./AddSelfSignedToFirefox)

## Generating Real SSL Certificate using Certbot

1. [Install Certbot](https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal&commit=%3E)
Use this direct link for NGINX on Ubuntu 20.xx

2. Obtain and install SSL Certificate using Certbot
```bash
docker exec -ti <nginx_conatiner_id> /bin/bash $(which certbot) certonly --nginx -d <your_live_domain.com>
```

3. Configure NGINX to Use the Real SSL Certificate
Certbot will automatically configure NGINX to use the obtained SSL certificate. You can find the certificate and key files in the Certbot directory, usually located in /etc/letsencrypt/live/your_domain.com/.

Check that your NGINX configuration was updated to use SSL certificate:

```nginx configuration
server {
    listen 443 ssl;
    server_name your_live_domain.com;

    ssl_certificate /etc/letsencrypt/live/your_live_domain.com/server.crt;
    ssl_certificate_key /etc/letsencrypt/live/your_live_domain.com/server.key;

    # ...
}
```
