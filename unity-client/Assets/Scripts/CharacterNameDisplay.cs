using UnityEngine;
using UnityEngine.UI;

public class CharacterNameDisplay : MonoBehaviour
{
    public static CharacterNameDisplay Instance;

    public Text nameText;

    void Awake()
    {
        Instance = this;
    }

    public void ShowName(string newName)
    {
        nameText.text = newName;
    }
}
