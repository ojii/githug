# -*- coding: utf-8 -*-
from app import app # connects to mongodb
import argparse
from models import Hug, User

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

    args = parser.parse_args()

    args.func(args)
