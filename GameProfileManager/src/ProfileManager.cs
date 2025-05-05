using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;

namespace GameProfileManager
{
    public class ProfileManager
    {
        private readonly string profilesDirectory;

        public ProfileManager(string profilesDirectory)
        {
            this.profilesDirectory = profilesDirectory;
            Directory.CreateDirectory(profilesDirectory);
        }

        public void CreateProfile(string gameName, string configPath)
        {
            var profile = new GameProfile
            {
                GameName = gameName,
                ConfigPath = configPath,
                ProfileData = new Dictionary<string, string>()
            };

            SaveProfile(profile);
        }

        public GameProfile LoadProfile(string gameName)
        {
            var profilePath = GetProfilePath(gameName);
            if (File.Exists(profilePath))
            {
                var json = File.ReadAllText(profilePath);
                return JsonConvert.DeserializeObject<GameProfile>(json);
            }
            throw new FileNotFoundException($"Profile for {gameName} not found.");
        }

        public void SaveProfile(GameProfile profile)
        {
            var profilePath = GetProfilePath(profile.GameName);
            var json = JsonConvert.SerializeObject(profile, Formatting.Indented);
            File.WriteAllText(profilePath, json);
        }

        private string GetProfilePath(string gameName)
        {
            return Path.Combine(profilesDirectory, $"{gameName}.json");
        }
    }
}