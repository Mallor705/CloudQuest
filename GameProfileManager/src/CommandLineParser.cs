using System;
using System.Collections.Generic;

namespace GameProfileManager
{
    public class CommandLineParser
    {
        public string ConfigPath { get; private set; }
        public string NewGameProfile { get; private set; }
        public string GameProfile { get; private set; }
        public bool IsNewGame { get; private set; }

        public CommandLineParser(string[] args)
        {
            ParseArguments(args);
        }

        private void ParseArguments(string[] args)
        {
            for (int i = 0; i < args.Length; i++)
            {
                switch (args[i])
                {
                    case "--config":
                        if (i + 1 < args.Length)
                        {
                            ConfigPath = args[++i];
                        }
                        else
                        {
                            throw new ArgumentException("Missing value for --config option.");
                        }
                        break;

                    case "--newgame":
                        IsNewGame = true;
                        if (i + 1 < args.Length)
                        {
                            NewGameProfile = args[++i];
                        }
                        else
                        {
                            throw new ArgumentException("Missing value for --newgame option.");
                        }
                        break;

                    case "--eldenring":
                        GameProfile = "eldenring";
                        break;

                    case "--darksouls":
                        GameProfile = "darksouls";
                        break;

                    default:
                        throw new ArgumentException($"Unknown argument: {args[i]}");
                }
            }
        }

        public void Validate()
        {
            if (IsNewGame && string.IsNullOrEmpty(NewGameProfile))
            {
                throw new ArgumentException("New game profile name must be provided with --newgame.");
            }

            if (string.IsNullOrEmpty(ConfigPath) && string.IsNullOrEmpty(GameProfile))
            {
                throw new ArgumentException("Either --config or a game profile must be specified.");
            }
        }
    }
}