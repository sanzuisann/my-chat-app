using UnityEngine;
using UnityEngine.UI;

public class CharacterNameDisplay : MonoBehaviour
{
    public static CharacterNameDisplay Instance;

    public Text nameText;

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Debug.LogWarning("Duplicate CharacterNameDisplay detected, destroying this instance.");
            Destroy(this.gameObject);
            return;
        }
        Instance = this;
    }

    void OnDestroy()
    {
        if (Instance == this)
        {
            Instance = null;
        }
    }

    public void ShowName(string newName)
    {
        if (nameText == null)
        {
            Debug.LogWarning("nameText is not assigned.");
            return;
        }
        nameText.text = newName;
    }
}
