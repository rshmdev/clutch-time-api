from nba_client import NBAClient
from analytics import NBAAnalytics
import pandas as pd
import sys

def print_header(title):
    print("\n" + "="*50)
    print(f" {title.upper()} ".center(50, "="))
    print("="*50)

def main():
    client = NBAClient()
    analytics = NBAAnalytics()

    print_header("NBA Betting Analytics Tool")
    
    while True:
        print("\nMenu Principal:")
        print("1. Ver jogos de hoje")
        print("2. Analisar confronto específico")
        print("3. Ver estatísticas de um time")
        print("4. Sair")
        
        choice = input("\nEscolha uma opção: ")

        if choice == '1':
            games = client.get_todays_games()
            if games.empty:
                print("Nenhum jogo encontrado para hoje.")
            else:
                print_header("Jogos de Hoje")
                for _, game in games.iterrows():
                    home = client.get_team_name_by_id(game['HOME_TEAM_ID'])
                    away = client.get_team_name_by_id(game['VISITOR_TEAM_ID'])
                    print(f"{away} @ {home} | Status: {game['GAME_STATUS_TEXT']}")

        elif choice == '2':
            home_name = input("Time da casa (Nome ou Sigla): ")
            away_name = input("Time visitante (Nome ou Sigla): ")
            
            home_id = client.get_team_id(home_name)
            away_id = client.get_team_id(away_name)
            
            if not home_id or not away_id:
                print("Um ou ambos os times não foram encontrados.")
                continue
            
            print(f"\nAnalisando: {away_name} vs {home_name}...")
            
            home_recent = client.get_recent_games(home_id)
            away_recent = client.get_recent_games(away_id)
            
            analysis = analytics.analyze_matchup(None, None, home_recent, away_recent)
            
            print_header(f"Análise: {away_name} @ {home_name}")
            print(f"{'Métrica':<15} | {'Casa (Home)':<15} | {'Fora (Away)':<15}")
            print("-" * 50)
            
            metrics = [('Record (L10)', 'record'), ('PTS/G', 'PTS'), ('FG%', 'FG_PCT'), ('3P%', 'FG3_PCT'), ('REB', 'REB')]
            for label, key in metrics:
                h_val = analysis['home_form'].get(key, 'N/A')
                a_val = analysis['away_form'].get(key, 'N/A')
                
                if isinstance(h_val, float):
                    print(f"{label:<15} | {h_val:<15.2f} | {a_val:<15.2f}")
                else:
                    print(f"{label:<15} | {h_val:<15} | {a_val:<15}")
            
            print("-" * 50)
            print(f"Total de Pontos Esperado (L10): {analysis['total_expected_pts']:.2f}")
            print(f"Vantagem de Pontos (Home): {analysis['ppg_diff']:.2f}")

        elif choice == '3':
            team_name = input("Nome do time: ")
            team_id = client.get_team_id(team_name)
            if team_id:
                recent = client.get_recent_games(team_id)
                stats = analytics.calculate_averages(recent)
                print_header(f"Estatísticas Recentes: {team_name}")
                for k, v in stats.items():
                    print(f"{k}: {v}")
            else:
                print("Time não encontrado.")

        elif choice == '4':
            print("Saindo... Boa sorte nas apostas!")
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
