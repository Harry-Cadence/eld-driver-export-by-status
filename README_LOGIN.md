# Simple Login System for Streamlit App

This app now includes a simple login system with username "admin" and password "admin321".

## Local Development Setup

### Option 1: Using .streamlit/secrets.toml (Recommended)
1. Create a `.streamlit` folder in your project root
2. Create a `secrets.toml` file inside it with:
```toml
LOGIN_USERNAME = "admin"
LOGIN_PASSWORD = "admin321"
```

### Option 2: Using Environment Variables
Create a `.env` file in your project root with:
```
LOGIN_USERNAME=admin
LOGIN_PASSWORD=admin321
```

## Cloud Deployment (Streamlit Cloud)

1. Go to your Streamlit Cloud dashboard
2. Navigate to your app's settings
3. Go to the "Secrets" section
4. Add the following secrets:
   - `LOGIN_USERNAME` = `admin`
   - `LOGIN_PASSWORD` = `admin321`

## How to Use

1. Run your app locally: `streamlit run app.py`
2. You'll see a login page first
3. Enter username: `admin` and password: `admin321`
4. After successful login, you'll see the main app
5. Use the logout button in the sidebar to log out

## Security Notes

- This is a simple implementation for basic access control
- Credentials are stored in Streamlit secrets (encrypted in cloud)
- For production, consider using more secure authentication methods
- The default credentials are hardcoded as fallback for local development

## Testing

- **Local**: The app will work with the default credentials even without setting up secrets
- **Cloud**: Make sure to add the secrets in Streamlit Cloud dashboard
