
import json
import pandas as pd


from ..data import  get_results_shooter
from ..fb import send_text
from pathlib import Path
logger = logging.getLogger(__name__)

from django.conf import settings
from django.utils import timezone

from pathlib import Path
from ...backend.models import ShooterResults

from .parser import build_html


DATA_DIR = Path(__file__).absolute().parent.parent


def update_shooter_database():

    shooter = get_results_shooter()

    for index, row in shooter.iterrows():
        if not ShooterResults.objects.filter(comp_id=row['comp_id']).exists():
            ShooterResults.objects.create(comp_id=row['comp_id'])

            item = ShooterResults.objects.get(comp_id=row['comp_id'])

            item.weapon = row['comp_id'][:2]
            item.buli =row['comp_id'].split(' ')[0][2:]
            item.region = row['comp_id'].split(' ')[1][:-2]

            item.host = '-'

            item.postion = row['position']
            item.first_name = row['first_name']
            item.last_name =row['last_name']
            item.team_full =row['team_full']
            item.team_short = row['team_short']
            item.result = row['result']
            item.shoot_off = row['shoot_off']

            item.point = row['point']
            item.save()



