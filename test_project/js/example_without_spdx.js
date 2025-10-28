// This is a JavaScript file without SPDX license declaration
// Testing the scanner's ability to detect missing licenses

const config = {
    apiUrl: "https://api.example.com",
    timeout: 5000,
    retries: 3
};

class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async fetch(endpoint) {
        const url = `${this.baseURL}${endpoint}`;
        try {
            const response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { config, APIClient };
}