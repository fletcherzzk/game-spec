// Local development default. GitHub Actions replaces this file in the Pages artifact.
// For manual hosting, set backendUrl to your Render HTTPS origin (no /socket.io path).
window.BUGHOUSE_CONFIG = {
  backendUrl: ['localhost', '127.0.0.1'].includes(window.location.hostname)
    ? 'http://localhost:5000'
    : ''
};
