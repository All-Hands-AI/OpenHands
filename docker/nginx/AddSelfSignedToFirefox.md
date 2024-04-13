# Add Self-Signed Certificate to the Client Web Browser

When you access your website in a web browser, it may display a warning about the self-signed certificate. You can add the self-signed certificate to the list of trusted certificates in your browser's settings to bypass the warning.

## Export the Certificate

First, you need to export the self-signed certificate from your server.

- If you're using OpenSSL, you can typically find your certificate in .crt or .pem format.
- If you generated the certificate using a tool or service, refer to its documentation for instructions on how to export the certificate.

## Import the Certificate into Firefox Developer Edition

1. Open [Firefox Developer Edition](https://www.mozilla.org/en-US/firefox/developer/).
2. Click on the menu button (three horizontal lines) at the top-right corner to open the Firefox menu.
3. Select Preferences.
4. In the Preferences tab, scroll down and click on Privacy & Security.
5. Scroll down to the Certificates section and click on View Certificates.
6. In the Certificate Manager window, go to the Authorities tab.
7. Click on Import and select the certificate file (.crt or .pem) that you exported.
8. Follow the on-screen instructions to import the certificate.

You may be prompted to enter your computer's password to authorize the certificate import.

## Trust the Certificate

After importing the certificate, Firefox will prompt you to confirm that you want to trust the certificate authority. You'll need to confirm that you trust the certificate authority to proceed.

## Verify Certificate Installation

After importing the certificate, verify that it has been successfully added to Firefox:

Close and reopen Firefox to apply the changes.
Visit the website secured with the self-signed certificate. Firefox should now trust the certificate and not display any security warnings.

