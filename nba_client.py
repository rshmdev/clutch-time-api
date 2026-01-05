from nba_api.stats.static import teams
from nba_api.stats.endpoints import scoreboardv3, BoxScoreSummaryV3
from nba_api.live.nba.endpoints import PlayByPlay, ScoreBoard
from typing import List, Dict, Any, Optional
import pandas as pd
import time
import datetime
import sys

class NBAClient:
    def __init__(self):
        self.teams = teams.get_teams()
        self.teams_dict = {team['id']: team for team in self.teams}
        self.headers = {
            'Host': 'stats.nba.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://stats.nba.com/'
        }

    def _get_today_et(self) -> str:
        """
        Retorna a data de hoje no formato MM/DD/YYYY no timezone ET (Eastern Time).
        ET é UTC-5 (EST) ou UTC-4 (EDT durante daylight saving).
        Durante a temporada da NBA (outubro a junho), geralmente é EST (UTC-5).
        """
        # Obter UTC agora
        utc_now = datetime.datetime.utcnow()
        # ET pode ser UTC-4 (EDT) ou UTC-5 (EST)
        # Durante a temporada da NBA (outubro a junho), geralmente é EST (UTC-5)
        est_offset = datetime.timedelta(hours=-5)
        et_now = utc_now + est_offset
        return et_now.strftime('%m/%d/%Y')

    def get_games_by_date(self, game_date: str) -> List[Dict[str, Any]]:
        """
        Busca jogos de uma data específica usando ScoreboardV2.
        
        Args:
            game_date: Data no formato 'YYYY-MM-DD'
            
        Returns:
            Lista de jogos com informações básicas
        """
        try:
            # Converter data para formato esperado pela API
            date_obj = datetime.datetime.strptime(game_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%m/%d/%Y')

            # Usar data de hoje no timezone ET
            today_et = self._get_today_et()
            if formatted_date == today_et:
                # Usar endpoint ao vivo para jogos de hoje
                scoreboard = ScoreBoard()
            else:
                scoreboard = scoreboardv3.ScoreboardV3(game_date=formatted_date)   
            # Chamar ScoreboardV3
            data = scoreboard.get_dict()
            games_list = data['scoreboard']['games']
            
            games = []
            for game in games_list:
                game_info = {
                    'gameId': str(game['gameId']),
                    'gameDate': game_date,
                    'homeTeamId': int(game['homeTeam']['teamId']),
                    'homeTeamName': self._get_team_name(game['homeTeam']['teamId']),
                    'homeTeamAbbr': self._get_team_abbr(game['homeTeam']['teamId']),
                    'awayTeamId': int(game['awayTeam']['teamId']),
                    'awayTeamName': self._get_team_name(game['awayTeam']['teamId']),
                    'awayTeamAbbr': self._get_team_abbr(game['awayTeam']['teamId']),
                    'status': self._parse_game_status(game['gameStatus']),
                    'homeScore': int(game['homeTeam']['score']),
                    'awayScore': int(game['awayTeam']['score']),
                    'quarter': int(game['period']),
                    'timeRemaining': str(game['gameClock']),
                    'arena': '',
                    'broadcaster': '',
                }
                games.append(game_info)
            
            return games
        except Exception as e:
            print(f"Error fetching games for {game_date}: {str(e)}", file=sys.stderr)
            return []

    def get_game_details(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca detalhes completos de um jogo usando BoxScoreSummaryV3.
        Para jogos ao vivo, usa ScoreBoard() similar a get_games_by_date.
        
        Args:
            game_id: ID do jogo
            
        Returns:
            Dicionário com detalhes do jogo
        """
        try:
            # Primeiro, verificar se o jogo está ao vivo usando ScoreBoard
            try:
                scoreboard = ScoreBoard()
                scoreboard_data = scoreboard.get_dict()
                games_list = scoreboard_data['scoreboard']['games']
                
                # Procurar o jogo específico no scoreboard
                live_game = None
                for game in games_list:
                    if str(game['gameId']) == game_id:
                        live_game = game
                        # Se o jogo está ao vivo (status == 2 = "live"), usar ScoreBoard
                        status_parsed = self._parse_game_status(game['gameStatus'])
                        if status_parsed == "live":
                            return self._build_game_details_from_scoreboard(live_game)
                        break
            except Exception as e:
                # Se ScoreBoard falhar, continuar com BoxScoreSummaryV3
                pass
            
            # Se não encontrou ou não está ao vivo, usar BoxScoreSummaryV3
            box_score = BoxScoreSummaryV3(game_id=game_id)
            data = box_score.get_dict()
            game = data['boxScoreSummary']
            
            # Processar line score from homeTeam and awayTeam periods
            line_score_data = []
            
            # Home team line score
            home_periods = game['homeTeam']['periods']
            home_line = {
                'teamId': game['homeTeam']['teamId'],
                'teamAbbr': game['homeTeam']['teamTricode'],
                'q1': home_periods[0]['score'] if len(home_periods) > 0 else 0,
                'q2': home_periods[1]['score'] if len(home_periods) > 1 else 0,
                'q3': home_periods[2]['score'] if len(home_periods) > 2 else 0,
                'q4': home_periods[3]['score'] if len(home_periods) > 3 else 0,
                'ot1': home_periods[4]['score'] if len(home_periods) > 4 else 0,
                'ot2': home_periods[5]['score'] if len(home_periods) > 5 else 0,
                'total': game['homeTeam']['score'],
            }
            line_score_data.append(home_line)
            
            # Away team line score
            away_periods = game['awayTeam']['periods']
            away_line = {
                'teamId': game['awayTeam']['teamId'],
                'teamAbbr': game['awayTeam']['teamTricode'],
                'q1': away_periods[0]['score'] if len(away_periods) > 0 else 0,
                'q2': away_periods[1]['score'] if len(away_periods) > 1 else 0,
                'q3': away_periods[2]['score'] if len(away_periods) > 2 else 0,
                'q4': away_periods[3]['score'] if len(away_periods) > 3 else 0,
                'ot1': away_periods[4]['score'] if len(away_periods) > 4 else 0,
                'ot2': away_periods[5]['score'] if len(away_periods) > 5 else 0,
                'total': game['awayTeam']['score'],
            }
            line_score_data.append(away_line)
            
            return {
                'gameId': str(game['gameId']),
                'gameCode': str(game['gameCode']),
                'status': self._parse_game_status(game['gameStatus']),
                'statusText': str(game['gameStatusText']),
                'period': int(game['period']),
                'gameClock': str(game['gameClock']),
                'gameTimeUTC': str(game['gameTimeUTC']),
                'gameEt': str(game['gameEt']),
                'duration': str(game['duration']),
                'arena': {
                    'name': str(game['arena']['arenaName']),
                    'city': str(game['arena']['arenaCity']),
                    'state': str(game['arena']['arenaState']),
                    'country': str(game['arena']['arenaCountry']),
                },
                'attendance': int(game['attendance']),
                'homeTeam': {
                    'teamId': int(game['homeTeam']['teamId']),
                    'teamName': str(game['homeTeam']['teamName']),
                    'teamCity': str(game['homeTeam']['teamCity']),
                    'teamTricode': str(game['homeTeam']['teamTricode']),
                    'wins': int(game['homeTeam']['teamWins']),
                    'losses': int(game['homeTeam']['teamLosses']),
                    'score': int(game['homeTeam']['score']),
                    'periods': game['homeTeam']['periods'],
                    'players': game['homeTeam']['players'],
                    'inactives': game['homeTeam']['inactives'],
                },
                'awayTeam': {
                    'teamId': int(game['awayTeam']['teamId']),
                    'teamName': str(game['awayTeam']['teamName']),
                    'teamCity': str(game['awayTeam']['teamCity']),
                    'teamTricode': str(game['awayTeam']['teamTricode']),
                    'wins': int(game['awayTeam']['teamWins']),
                    'losses': int(game['awayTeam']['teamLosses']),
                    'score': int(game['awayTeam']['score']),
                    'periods': game['awayTeam']['periods'],
                    'players': game['awayTeam']['players'],
                    'inactives': game['awayTeam']['inactives'],
                },
                'officials': game['officials'],
                'lastFiveMeetings': game['lastFiveMeetings'],
                'lineScore': line_score_data,
            }
        except Exception as e:
            print(f"Error fetching game details for {game_id}: {str(e)}", file=sys.stderr)
            return None

    def _build_game_details_from_scoreboard(self, game: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constrói detalhes do jogo a partir dos dados do ScoreBoard (para jogos ao vivo).
        
        Args:
            game: Dicionário com dados do jogo do ScoreBoard
            
        Returns:
            Dicionário com detalhes do jogo no formato esperado
        """
        # Processar períodos para line score
        home_periods = game['homeTeam'].get('periods', [])
        away_periods = game['awayTeam'].get('periods', [])
        
        line_score_data = []
        
        # Home team line score
        home_line = {
            'teamId': game['homeTeam']['teamId'],
            'teamAbbr': self._get_team_abbr(game['homeTeam']['teamId']),
            'q1': home_periods[0]['score'] if len(home_periods) > 0 else 0,
            'q2': home_periods[1]['score'] if len(home_periods) > 1 else 0,
            'q3': home_periods[2]['score'] if len(home_periods) > 2 else 0,
            'q4': home_periods[3]['score'] if len(home_periods) > 3 else 0,
            'ot1': home_periods[4]['score'] if len(home_periods) > 4 else 0,
            'ot2': home_periods[5]['score'] if len(home_periods) > 5 else 0,
            'total': game['homeTeam']['score'],
        }
        line_score_data.append(home_line)
        
        # Away team line score
        away_line = {
            'teamId': game['awayTeam']['teamId'],
            'teamAbbr': self._get_team_abbr(game['awayTeam']['teamId']),
            'q1': away_periods[0]['score'] if len(away_periods) > 0 else 0,
            'q2': away_periods[1]['score'] if len(away_periods) > 1 else 0,
            'q3': away_periods[2]['score'] if len(away_periods) > 2 else 0,
            'q4': away_periods[3]['score'] if len(away_periods) > 3 else 0,
            'ot1': away_periods[4]['score'] if len(away_periods) > 4 else 0,
            'ot2': away_periods[5]['score'] if len(away_periods) > 5 else 0,
            'total': game['awayTeam']['score'],
        }
        line_score_data.append(away_line)
        
        # Construir resposta no formato esperado
        # Nota: ScoreBoard não tem todos os campos detalhados do BoxScoreSummaryV3
        return {
            'gameId': str(game['gameId']),
            'gameCode': str(game.get('gameCode', '')),
            'status': self._parse_game_status(game['gameStatus']),
            'statusText': game.get('gameStatusText', ''),
            'period': int(game.get('period', 0)),
            'gameClock': str(game.get('gameClock', '')),
            'gameTimeUTC': str(game.get('gameTimeUTC', '')),
            'gameEt': str(game.get('gameEt', '')),
            'duration': str(game.get('duration', '')),
            'arena': {
                'name': game.get('arena', {}).get('arenaName', '') if isinstance(game.get('arena'), dict) else '',
                'city': game.get('arena', {}).get('arenaCity', '') if isinstance(game.get('arena'), dict) else '',
                'state': game.get('arena', {}).get('arenaState', '') if isinstance(game.get('arena'), dict) else '',
                'country': game.get('arena', {}).get('arenaCountry', '') if isinstance(game.get('arena'), dict) else '',
            },
            'attendance': int(game.get('attendance', 0)) if game.get('attendance') else 0,
            'homeTeam': {
                'teamId': int(game['homeTeam']['teamId']),
                'teamName': self._get_team_name(game['homeTeam']['teamId']),
                'teamCity': self._get_team_name(game['homeTeam']['teamId']).split()[-1] if self._get_team_name(game['homeTeam']['teamId']) else '',
                'teamTricode': self._get_team_abbr(game['homeTeam']['teamId']),
                'wins': int(game['homeTeam'].get('wins', 0)) if game['homeTeam'].get('wins') else 0,
                'losses': int(game['homeTeam'].get('losses', 0)) if game['homeTeam'].get('losses') else 0,
                'score': int(game['homeTeam']['score']),
                'periods': home_periods,
                'players': game['homeTeam'].get('players', []),
                'inactives': game['homeTeam'].get('inactives', []),
            },
            'awayTeam': {
                'teamId': int(game['awayTeam']['teamId']),
                'teamName': self._get_team_name(game['awayTeam']['teamId']),
                'teamCity': self._get_team_name(game['awayTeam']['teamId']).split()[-1] if self._get_team_name(game['awayTeam']['teamId']) else '',
                'teamTricode': self._get_team_abbr(game['awayTeam']['teamId']),
                'wins': int(game['awayTeam'].get('wins', 0)) if game['awayTeam'].get('wins') else 0,
                'losses': int(game['awayTeam'].get('losses', 0)) if game['awayTeam'].get('losses') else 0,
                'score': int(game['awayTeam']['score']),
                'periods': away_periods,
                'players': game['awayTeam'].get('players', []),
                'inactives': game['awayTeam'].get('inactives', []),
            },
            'officials': game.get('officials', []),
            'lastFiveMeetings': game.get('lastFiveMeetings', []),
            'lineScore': line_score_data,
        }

    def get_play_by_play(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Busca eventos do play-by-play usando PlayByPlayV2.
        
        Args:
            game_id: ID do jogo
            
        Returns:
            Lista de eventos do jogo
        """
        try:
            pbp = PlayByPlay(game_id=game_id)
            data = pbp.get_dict()
            actions = data['game']['actions']
            
            events = []
            for action in actions:
                event_info = {
                    'actionNumber': int(action['actionNumber']),
                    'actionType': str(action['actionType']),
                    'subType': str(action.get('subType', '')),
                    'descriptor': str(action.get('descriptor', '')),
                    'clock': str(action['clock']),
                    'period': int(action['period']),
                    'periodType': str(action['periodType']),
                    'teamId': int(action.get('teamId', 0)),
                    'teamTricode': str(action.get('teamTricode', '')),
                    'personId': int(action.get('personId', 0)),
                    'playerName': str(action.get('playerName', '')),
                    'playerNameI': str(action.get('playerNameI', '')),
                    'description': str(action.get('description', '')),
                    'scoreHome': str(action.get('scoreHome', '')),
                    'scoreAway': str(action.get('scoreAway', '')),
                    'possession': int(action.get('possession', 0)),
                    'timeActual': str(action.get('timeActual', '')),
                    'x': action.get('x'),
                    'y': action.get('y'),
                    'qualifiers': action.get('qualifiers', []),
                    'personIdsFilter': action.get('personIdsFilter', []),
                }
                events.append(event_info)
            
            return events
        except Exception as e:
            print(f"Error fetching play-by-play for {game_id}: {str(e)}", file=sys.stderr)
            return []

    def _parse_game_status(self, status_id: int) -> str:
        """Converte ID de status para string."""
        if status_id == 1:
            return "pre-live"
        elif status_id == 2:
            return "live"
        elif status_id == 3:
            return "finished"
        else:
            return "unknown"

    def _get_team_name(self, team_id: int) -> str:
        """Obtém nome do time pelo ID."""
        team = self.teams_dict.get(team_id)
        return team['full_name'] if team else f"Team {team_id}"

    def _get_team_abbr(self, team_id: int) -> str:
        """Obtém abreviação do time pelo ID."""
        team = self.teams_dict.get(team_id)
        return team['abbreviation'] if team else "UNK"