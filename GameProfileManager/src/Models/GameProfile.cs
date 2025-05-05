using System;
using System.IO;
using Newtonsoft.Json;

namespace GameProfileManager.Models
{
    public class GameProfile
    {
        public string GameName { get; set; }
        public string ConfigPath { get; set; }
        public string ProfileData { get; set; }

        public GameProfile(string gameName, string configPath, string profileData)
        {
            GameName = gameName;
            ConfigPath = configPath;
            ProfileData = profileData;
        }

        public void SaveProfile(string filePath)
        {
            var json = JsonConvert.SerializeObject(this, Formatting.Indented);
            File.WriteAllText(filePath, json);
        }

        public static GameProfile LoadProfile(string filePath)
        {
            var json = File.ReadAllText(filePath);
            return JsonConvert.DeserializeObject<GameProfile>(json);
        }
    }
}