# URnetwork Provider Add-on

**[中文版 README](https://github.com/harry2690/urnetwork-homeassistant-addon/blob/main/README_CN.md)**

Turn your Home Assistant into a URnetwork provider, contribute to the decentralized network and earn USDC rewards.

## Installation Steps

### 1. Add Add-on Repository

In Home Assistant:

1. Go to **Settings** → **Add-ons** → **Add-on Store**
2. Click the three-dot menu in the top right corner
3. Select **Repositories**
4. Add this repository URL: `https://github.com/harry2690/urnetwork-homeassistant-addon`
5. Click **Add**

### 2. Install Add-on

1. Refresh the Add-on Store
2. Find **URnetwork Provider**
3. Click **Install**
4. Wait for installation to complete

### 3. Important: Disable Protection Mode

⚠️ **This step is critical** - URnetwork Add-on requires Docker access to manage containers

1. In the Add-on page, click the **Configuration** tab
2. **Turn off "Protection mode"** option
3. Click **Save**

### 4. Start Add-on

1. Return to the **Info** tab
2. Click **Start**
3. Optional: Enable **Start on boot** for automatic startup
4. Optional: Enable **Watchdog** for automatic restart

## Configuration Options

You can adjust the following settings in the Add-on's **Configuration** page:

```yaml
ssl: false                 # Whether to enable SSL
certfile: fullchain.pem    # SSL certificate file
keyfile: privkey.pem       # SSL private key file
web_port: 8099            # Web UI port
log_level: info           # Log level (trace/debug/info/notice/warning/error/fatal)
```

### Default Configuration

In most cases, the default settings work fine. You don't need to modify the configuration unless you have special requirements.

## Authentication Process

### 1. Get Authentication Code

1. Visit [ur.io](https://ur.io)
2. Register or log in to your account
3. Get your Authentication Code

### 2. Initial Authentication

1. After starting the Add-on, click **Open Web UI**
2. You'll see the setup page
3. Enter the authentication code from ur.io
4. Click **Authenticate**
5. Wait for authentication to complete

### 3. Re-authentication (if needed)

If you encounter authentication issues:

1. Click the **Re-authenticate** button in the Dashboard
2. Enter your original authentication code
3. The system will perform real Docker authentication
4. Restart the Provider container after completion

### 4. Verify Connection

After authentication:
- Check container status in the Dashboard
- Visit [ur.io](https://ur.io) to confirm your client shows as "Connected"
- Check system logs to ensure no authentication errors

## Web UI Features

Access the Web UI at `http://[HOME_ASSISTANT_IP]:8099`

- **Dashboard**: Monitor Provider status and rewards
- **Container Control**: Start, stop, restart, update URnetwork Provider
- **System Logs**: View runtime logs and error messages
- **Re-authentication**: Re-authenticate when encountering authentication issues

## Common Issues

### Container Won't Start

1. Confirm protection mode is disabled
2. Check if Docker service is running normally
3. Check Add-on logs for error messages

### Authentication Failure

1. Confirm authentication code is correct
2. Use "Re-authenticate" function
3. Confirm network connection is normal

### Cannot Access Web UI

1. Check port settings (default 8099)
2. Confirm firewall settings
3. Try restarting the Add-on

## Support & Feedback

### Report Issues

If you encounter problems:

1. Check Add-on logs
2. Report to [GitHub Issues](https://github.com/harry2690/urnetwork-homeassistant-addon/issues)
3. Provide detailed error messages and logs

### Sponsorship

Welcome to join ur.io with my referral code: [https://ur.io/app?bonus=J8C8CV](https://ur.io/app?bonus=J8C8CV)

Or buy me a coffee: [BASE Chain] 0x040F0037C6a4C28DC504d718Ca9329eFBF6fD8d1

### Community Support

- URnetwork Official Documentation: [ur.io](https://ur.io)
- Home Assistant Community Discussion

## License

This project is licensed under the MIT License.

### Third-party Licenses

- URnetwork Provider: Please refer to URnetwork official license terms
- Home Assistant Add-on Framework: Apache 2.0 License

---

**Disclaimer**: Before using this Add-on, please ensure you understand URnetwork's terms of service and privacy policy. Network provider services may consume your network bandwidth and electricity.