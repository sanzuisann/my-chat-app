using UnityEngine;
using UnityEngine.UI;  // ← UIを使う場合に必要！

public class EventFlag : MonoBehaviour
{
    public GameObject eventPanel;   // Inspectorに表示される
    public Text eventText;          // ↑ TextMeshPro使うなら別途対応

    public int currentValue = 0;
    public int threshold = 10;

    private bool eventTriggered = false;

    void Update()
    {
        if (!eventTriggered && currentValue >= threshold)
        {
            eventTriggered = true;
            ShowEventMessage();
        }
    }

    void ShowEventMessage()
    {
        if (eventPanel != null) eventPanel.SetActive(true);
        if (eventText != null) eventText.text = "内部値が溜まりました";
    }

    // デバッグ用加算
    public void AddValue(int amount)
    {
        currentValue += amount;
    }
}
