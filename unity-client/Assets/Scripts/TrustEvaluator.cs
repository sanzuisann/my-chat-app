using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections;

public class TrustEvaluator : MonoBehaviour
{
    [Header("UI参照")]
    public InputField inputField;  // ユーザー入力欄（ChatManagerのInputFieldをアサイン）

    [Header("API設定")]
    public string evaluateTrustUrl = ApiConfig.BaseUrl + "/evaluate-trust";

    [Header("ID設定（UUID形式）")]
    public string userId = "1f494426-588c-4a74-a5a0-6d9d1dafebec";
    public string characterId = "854d5e61-9d5c-45c6-b3b6-019acfba777e";

    [Header("連携スクリプト")]
    public ChatManager chatManager;  // ← Unityでアサイン

    /// <summary>
    /// ユーザーが入力欄に書いた内容を評価（ボタン連携用）
    /// </summary>
    public void EvaluateTrustFromInput()
    {
        string userMessage = inputField.text;

        if (string.IsNullOrWhiteSpace(userMessage))
        {
            Debug.LogWarning("⚠️ 入力が空です。評価をスキップします。");
            return;
        }

        StartCoroutine(PostEvaluateTrust(userMessage));
    }

    /// <summary>
    /// 任意のメッセージ文字列を評価（ChatManagerからの連携用）
    /// </summary>
    public void EvaluateTrust(string message)
    {
        if (string.IsNullOrWhiteSpace(message))
        {
            Debug.LogWarning("⚠️ メッセージが空のため、信頼度評価をスキップします。");
            return;
        }

        StartCoroutine(PostEvaluateTrust(message));
    }

    /// <summary>
    /// 評価APIにPOST送信
    /// </summary>
    IEnumerator PostEvaluateTrust(string userMessage)
    {
        string json = $"{{\"user_id\":\"{userId}\",\"character_id\":\"{characterId}\",\"player_message\":\"{userMessage}\"}}";

        Debug.Log("📤 送信するJSON: " + json);

        var request = new UnityWebRequest(evaluateTrustUrl, "POST");
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("✅ スコア取得成功: " + request.downloadHandler.text);

            // JSON → TrustResponse に変換してスコア取得
            TrustResponse response = JsonUtility.FromJson<TrustResponse>(request.downloadHandler.text);

            if (chatManager != null)
            {
                chatManager.SetTrust(response.trust_score); // ← ChatManagerにスコアを渡す
            }
            else
            {
                Debug.LogWarning("⚠️ chatManager が未アサインです。信頼度を表示できません。");
            }
        }
        else
        {
            Debug.LogError("❌ スコア取得失敗: " + request.responseCode + " - " + request.error);
            Debug.LogError("📥 サーバー応答内容: " + request.downloadHandler.text);
        }
    }
}

[System.Serializable]
public class TrustResponse
{
    public int trust_score;
}
