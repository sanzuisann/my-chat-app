using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;

public class CharacterClick : MonoBehaviour
{
    public string characterId;  // UUID文字列

    private void OnMouseDown()
    {
        StartCoroutine(FetchCharacterNameFromList());
    }

    IEnumerator FetchCharacterNameFromList()
    {
        string url = ApiConfig.BaseUrl + "/characters/";

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("キャラ一覧取得エラー: " + request.error);
            }
            else
            {
                string json = "{\"characters\":" + request.downloadHandler.text + "}";
                CharacterListWrapper list = JsonUtility.FromJson<CharacterListWrapper>(json);

                foreach (CharacterData c in list.characters)
                {
                    if (c.id == characterId)
                    {
                        CharacterNameDisplay.Instance.ShowName(c.name);
                        yield break;
                    }
                }

                Debug.LogWarning("指定したキャラIDが見つかりませんでした");
            }
        }
    }

    [System.Serializable]
    public class CharacterData
    {
        public string id;
        public string name;
        public string personality;
        public string system_prompt;
    }

    [System.Serializable]
    public class CharacterListWrapper
    {
        public List<CharacterData> characters;
    }
}
