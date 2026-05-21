# Extra NetBox configuration settings
# This file is loaded after the main configuration

DEBUG = True
ALLOWED_HOSTS = ['*']
LOGIN_REQUIRED = False
DEVELOPER = True

# API Token Peppers for v2 tokens (NetBox 4.5+)
# Required for v2 API tokens to work. Must be at least 50 characters.
API_TOKEN_PEPPERS = {
    1: 'devpepperkey1234567890abcdefghijklmnopqrstuvwxyz0123456789',
}
