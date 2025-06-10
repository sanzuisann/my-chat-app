using UnityEngine;
using UnityEngine.Tilemaps;

public class AutoTilePlacer : MonoBehaviour
{
    public Tilemap groundTilemap;   // 草・道を置くTilemap
    public TileBase grassTile;      // 草のタイル
    public TileBase roadTile;       // 道のタイル

    public int width = 30;          // マップの横幅
    public int height = 20;         // マップの高さ

    void Start()
    {
        GenerateGroundAndRoad();
    }

    void GenerateGroundAndRoad()
    {
        int mainX = width / 2;
        int mainY = height / 2;

        int extraX = width / 3;     // 追加交差点のX位置（例：10）
        int extraY = height / 3;    // 追加交差点のY位置（例：6）

        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                Vector3Int pos = new Vector3Int(x, y, 0);

                // 道の条件：中央 or 追加交差点の位置
                bool isRoad =
                    x == mainX || y == mainY ||  // 中央の交差点
                    x == extraX || y == extraY;  // 追加の交差点

                // 道なら roadTile、そうでなければ grassTile を配置
                groundTilemap.SetTile(pos, isRoad ? roadTile : grassTile);
            }
        }
    }
}
