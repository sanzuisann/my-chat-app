using UnityEngine;

public static class ApiConfig
{
    // Key name used for PlayerPrefs or environment variable
    private const string ConfigKey = "API_BASE_URL";

    // Default URL when no configuration is provided
    private const string DefaultUrl = "http://localhost:8000";

    // Base URL for all API requests
    public static string BaseUrl
    {
        get
        {
            // Check Unity's PlayerPrefs first
            string prefUrl = PlayerPrefs.GetString(ConfigKey);
            if (!string.IsNullOrEmpty(prefUrl))
            {
                return prefUrl;
            }

            // Fallback to environment variable
            string envUrl = System.Environment.GetEnvironmentVariable(ConfigKey);
            if (!string.IsNullOrEmpty(envUrl))
            {
                return envUrl;
            }

            // Default local development URL
            return DefaultUrl;
        }
    }
}
