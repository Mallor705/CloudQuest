using System;

namespace GameProfileManager
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length == 0)
            {
                Console.WriteLine("No command provided. Use --config, --newgame, --eldenring, or --darksouls.");
                return;
            }

            CommandLineParser parser = new CommandLineParser();
            var command = parser.Parse(args);

            switch (command)
            {
                case CommandLineOptions.Config:
                    // Handle configuration loading
                    Console.WriteLine("Loading configuration...");
                    break;

                case CommandLineOptions.NewGame:
                    // Handle new game profile creation
                    Console.WriteLine("Creating a new game profile...");
                    break;

                case CommandLineOptions.EldenRing:
                    // Handle Elden Ring specific profile
                    Console.WriteLine("Loading Elden Ring profile...");
                    break;

                case CommandLineOptions.DarkSouls:
                    // Handle Dark Souls specific profile
                    Console.WriteLine("Loading Dark Souls profile...");
                    break;

                default:
                    Console.WriteLine("Unknown command. Use --config, --newgame, --eldenring, or --darksouls.");
                    break;
            }
        }
    }
}