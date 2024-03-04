import json

from dateutil import parser

from processing.revenue import calculate_revenue_data_daily
from utility.api_manager import manager
from utility.util import json_serialize_datetime


def get_turnovers():
    result = []

    for user in manager.users:
        transfers = []

        for buy in manager.get_transfers_raw(user.id):
            if parser.parse(buy['date']) < manager.start:
                continue

            transfer_type = 'buy' if buy['type'] == 12 else 'sell'

            if 'bn' in buy['meta']:
                trade_partner = buy['meta']['bn']
            elif 'sn' in buy['meta']:
                trade_partner = buy['meta']['sn']
            else:
                trade_partner = 'Computer'

            transfers.append({'date': parser.parse(buy['date']),
                              'first_name': buy['meta']['pfn'],
                              'last_name': buy['meta']['pln'],
                              'value': buy['meta']['p'],
                              'type': transfer_type,
                              'trade_partner': trade_partner,
                              'team_id': buy['meta']['tid'],
                              'player_id': buy['meta']['pid'],
                              'user': user.name})

        # Remove duplicates given by api
        transfers = list({frozenset(item.items()): item for item in transfers}.values())

        transfers.reverse()

        turnovers = []

        for i, buy_transfer in enumerate(transfers):
            if buy_transfer['type'] == 'sell':
                continue

            for sell_transfer in transfers[i:]:
                if sell_transfer['type'] == 'buy':
                    continue

                if sell_transfer['player_id'] == buy_transfer['player_id']:
                    turnovers.append((buy_transfer, sell_transfer))
                    break

        # Revenue generated by randomly assigned players
        for transfer in transfers:
            if transfer['type'] == 'buy':
                continue

            if transfer not in [turnover[1] for turnover in turnovers]:
                date = manager.start
                buy_transfer = {'date': date,
                                'first_name': transfer['first_name'],
                                'last_name': transfer['last_name'],
                                'value': transfer['value'],
                                'type': 'buy',
                                'trade_partner': 'Computer',
                                'team_id': transfer['team_id'],
                                'player_id': transfer['player_id'],
                                'user': transfer['user']}

                turnovers.append((buy_transfer, transfer))

        result = result + turnovers

    with open('./data/turnovers.json', 'w') as f:
        f.writelines(json.dumps(result, default=json_serialize_datetime))

    calculate_revenue_data_daily(result)
