using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections;

public class ChatManager : MonoBehaviour
{
    [Header("UI参照")]
    public InputField inputField;     // ユーザー入力欄
    public Text responseText;         // GPTの返答表示欄
    public Text trustText;            // 信頼度スコア表示欄（パネル上に配置）

    [Header("API設定")]
    public string apiUrl = "https://my-chat-app-1-3wr3.onrender.com/chat";

    [Header("ID設定（UUID形式）")]
    public string userId = "1f494426-588c-4a74-a5a0-6d9d1dafebec";
    public string characterId = "854d5e61-9d5c-45c6-b3b6-019acfba777e";

    [Header("信頼度評価")]
    public TrustEvaluator trustEvaluator; // ← Unityでアサインする

    private int currentTrust = 0;

    void Start()
    {
        UpdateTrustDisplay(); // 起動時に初期表示
    }

    // ボタン押下時に呼び出される
    public void OnSendButtonClicked()
    {
        string message = inputField.text;
        if (!string.IsNullOrEmpty(message))
        {
            StartCoroutine(SendMessageToAPI(message));
        }
    }

    // GPTに送信する処理（POST）
    IEnumerator SendMessageToAPI(string message)
    {
        string jsonData = $"{{\"user_id\":\"{userId}\",\"character_id\":\"{characterId}\",\"user_message\":\"{message}\"}}";

        Debug.Log("📤 Chat送信JSON: " + jsonData);

        using (UnityWebRequest request = new UnityWebRequest(apiUrl, "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string responseJson = request.downloadHandler.text;
                ChatResponse response = JsonUtility.FromJson<ChatResponse>(responseJson);
                responseText.text = response.reply;

                if (trustEvaluator != null)
                {
                    trustEvaluator.EvaluateTrust(message);  // ← 評価実行
                }
                else
                {
                    Debug.LogWarning("⚠️ TrustEvaluator が未アサインです");
                }
            }
            else
            {
                responseText.text = $"エラー: HTTP/{request.responseCode}";
                Debug.LogError("❌ Chat送信失敗: " + request.error);
            }
        }
    }

    // TrustEvaluator から呼び出される想定の関数
    public void SetTrust(int trustScore)
    {
        currentTrust = trustScore;
        UpdateTrustDisplay();
    }

    // 信頼度スコアを UI に反映
    void UpdateTrustDisplay()
    {
        trustText.text = "信頼度: " + currentTrust.ToString();
    }
}

// GPTの返答JSON形式に対応（例: {"reply": "こんにちは"}）
[System.Serializable]
public class ChatResponse
{
    public string reply;
}
