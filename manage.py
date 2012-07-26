# -*- coding: utf-8 -*-
from app import app # connects to mongodb
import argparse
from models import Hug, User

def dailyhugs():
    for hug in Hug.objects.all():
        hug.day = hug.created.isoweekday()
        hug.save()

MIGRATIONS = {
    'dailyhugs': dailyhugs,
}

def migrate(args):
    MIGRATIONS[args.name]()

def clear(args):
    assert args.confirm
    Hug.objects().delete()
    User.objects().delete()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_clear = subparsers.add_parser('clear')
    parser_clear.add_argument('--confirm', action='store_true')
    parser_clear.set_defaults(func=clear)

    parser_clear = subparsers.add_parser('migrate')
    parser_clear.add_argument('name', choices=MIGRATIONS.keys())
    parser_clear.set_defaults(func=migrate)

    args = parser.parse_args()

    args.func(args)
