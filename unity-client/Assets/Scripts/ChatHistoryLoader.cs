using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;

public class ChatHistoryLoader : MonoBehaviour
{
    [Header("API設定")]
    public string historyUrl = ApiConfig.BaseUrl + "/history/{0}/{1}";
    public string userId = "1f494426-588c-4a74-a5a0-6d9d1dafebec";
    public string characterId = "854d5e61-9d5c-45c6-b3b6-019acfba777e";

    [Header("プレハブ")]
    public GameObject leftMessagePrefab;   // キャラ用
    public GameObject rightMessagePrefab;  // プレイヤー用

    [Header("ScrollViewのContent")]
    public Transform contentTransform; // ScrollView > Viewport > Content

    [System.Serializable]
    public class ChatEntry
    {
        public string speaker;   // "user" or "character"
        public string message;
        public string timestamp;
    }

    [System.Serializable]
    public class ChatEntryListWrapper
    {
        public ChatEntry[] history;
    }

    void Start()
    {
        StartCoroutine(LoadHistory());
    }

    IEnumerator LoadHistory()
    {
        string url = string.Format(historyUrl, userId, characterId);
        UnityWebRequest request = UnityWebRequest.Get(url);
        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("履歴取得に失敗: " + request.error);
            yield break;
        }

        string json = "{\"history\":" + request.downloadHandler.text + "}";
        ChatEntryListWrapper wrapper = JsonUtility.FromJson<ChatEntryListWrapper>(json);

        foreach (var entry in wrapper.history)
        {
            // 🔍 speaker ログ出力
            Debug.Log($"[履歴] speaker: {entry.speaker}, message: {entry.message}");

            // null 安全な speaker 判定
            string speaker = string.IsNullOrEmpty(entry.speaker) ? "unknown" : entry.speaker.ToLower();
            GameObject prefab = (speaker == "user") ? rightMessagePrefab : leftMessagePrefab;

            GameObject messageObj = Instantiate(prefab, contentTransform);

            Text text = messageObj.GetComponentInChildren<Text>();
            if (text != null)
            {
                text.text = entry.message;
            }
            else
            {
                Debug.LogWarning($"❗ Textが見つかりませんでした: {entry.message}");
            }
        }
    }
}
