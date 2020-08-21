import os
import sys
import argparse
import asyncio

import requests

sys.path.append(os.getcwd())

from krs.bootstrap import bootstrap, user_mgmt_app, get_token
from krs.groups import create_group
from krs.token import get_rest_client


GROUPS = {
    'institutions': {
        'IceCube': {},
        'IceCube-Gen2': {},
        'HAWC': {},
        'CTA': {},
        'ARA': {},
    },
    'experiments': {
        'IceCube': {
            'Working Groups': {},
        },
    },
    'posix': {},
    'tokens': {},
}

ICECUBE_INSTS = {
    'Aachen': {
        'cite': 'III. Physikalisches Institut, RWTH Aachen University, D-52056 Aachen, Germany',
    },
    'Adelaide': {
        'cite': 'Department of Physics, University of Adelaide, Adelaide, 5005, Australia',
    },
    'Alabama': {
        'cite': 'Dept. of Physics and Astronomy, University of Alabama, Tuscaloosa, AL 35487, USA',
    },
    'Alaska-Anchorage': {
        'cite': 'Dept. of Physics and Astronomy, University of Alaska Anchorage, 3211 Providence Dr., Anchorage, AK 99508, USA',
    },
    'Alberta': {
        'cite': 'Dept. of Physics, University of Alberta, Edmonton, Alberta, Canada T6G 2E1',
    },
    'Berlin': {
        'cite': 'Institut für Physik, Humboldt-Universität zu Berlin, D-12489 Berlin, Germany',
    },
    'Bochum': {
        'cite': 'Fakultät für Physik & Astronomie, Ruhr-Universität Bochum, D-44780 Bochum, Germany',
    },
    'Brussels-ULB': {
        'cite': 'Université Libre de Bruxelles, Science Faculty CP230, B-1050 Brussels, Belgium',
    },
    'Brussels-VUB': {
        'cite': 'Vrije Universiteit Brussel (VUB), Dienst ELEM, B-1050 Brussels, Belgium',
    },
    'Canterbury': {
        'cite': 'Dept. of Physics and Astronomy, University of Canterbury, Private Bag 4800, Christchurch, New Zealand',
    },
    'Chiba': {
        'cite': 'Dept. of Physics and Institute for Global Prominent Research, Chiba University, Chiba 263-8522, Japan',
    },
    'Clark-Atlanta': {
        'cite': 'CTSPS, Clark-Atlanta University, Atlanta, GA 30314, USA',
    },
    'Copenhagen': {
        'cite': 'Niels Bohr Institute, University of Copenhagen, DK-2100 Copenhagen, Denmark',
    },
    'Delaware': {
        'cite': 'Bartol Research Institute and Dept. of Physics and Astronomy, University of Delaware, Newark, DE 19716, USA',
    },
    'DESY': {
        'cite': 'DESY, D-15738 Zeuthen, Germany',
    },
    'Dortmund': {
        'cite': 'Dept. of Physics, TU Dortmund University, D-44221 Dortmund, Germany',
    },
    'Drexel': {
        'cite': 'Dept. of Physics, Drexel University, 3141 Chestnut Street, Philadelphia, PA 19104, USA',
    },
    'Erlangen': {
        'cite': 'Erlangen Centre for Astroparticle Physics, Friedrich-Alexander-Universität Erlangen-Nürnberg, D-91058 Erlangen, Germany',
    },
    'Harvard': {
        'cite': 'Department of Physics and Laboratory for Particle Physics and Cosmology, Harvard University, Cambridge, MA 02138, USA',
    },
    'GaTech': {
        'cite': 'School of Physics and Center for Relativistic Astrophysics, Georgia Institute of Technology, Atlanta, GA 30332, USA',
    },
    'Geneva': {
        'cite': 'Département de physique nucléaire et corpusculaire, Université de Genève, CH-1211 Genève, Switzerland',
    },
    'Gent': {
        'cite': 'Dept. of Physics and Astronomy, University of Gent, B-9000 Gent, Belgium',
    },
    'Kansas': {
        'cite': 'Dept. of Physics and Astronomy, University of Kansas, Lawrence, KS 66045, USA',
    },
    'Karlsruhe': {
        'cite': 'Karlsruhe Institute of Technology, Institut für Kernphysik, D-76021 Karlsruhe, Germany',
    },
    'LBNL': {
        'cite': 'Lawrence Berkeley National Laboratory, Berkeley, CA 94720, USA',
    },
    'Loyola': {
        'cite': 'Department of Physics, Loyola University Chicago, Chicago, IL 60660, USA',
    },
    'Mainz': {
        'cite': 'Institute of Physics, University of Mainz, Staudinger Weg 7, D-55099 Mainz, Germany',
    },
    'Marquette': {
        'cite': 'Department of Physics, Marquette University, Milwaukee, WI, 53201, USA',
    },
    'Maryland': {
        'cite': 'Dept. of Physics, University of Maryland, College Park, MD 20742, USA',
    },
    'Mercer': {
        'cite': 'Department of Physics, Mercer University, Macon, GA 31207-0001, USA',
    },
    'Michigan-State': {
        'cite': 'Dept. of Physics and Astronomy, Michigan State University, East Lansing, MI 48824, USA',
    },
    'MIT': {
        'cite': 'Dept. of Physics, Massachusetts Institute of Technology, Cambridge, MA 02139, USA',
    },
    'Munich': {
        'cite': 'Physik-department, Technische Universität München, D-85748 Garching, Germany',
    },
    'Munster': {
        'cite': 'Institut für Kernphysik, Westfälische Wilhelms-Universität Münster, D-48149 Münster, Germany',
    },
    'Ohio-State-Astronomy': {
        'cite': 'Dept. of Astronomy, Ohio State University, Columbus, OH 43210, USA',
    },
    'Ohio-State-Physics': {
        'cite': 'Dept. of Physics and Center for Cosmology and Astro-Particle Physics, Ohio State University, Columbus, OH 43210, USA',
    },
    'Oxford': {
        'cite': 'Dept. of Physics, University of Oxford, Parks Road, Oxford OX1 3PU, UK',
    },
    'Penn-State-Astronomy': {
        'cite': 'Dept. of Astronomy and Astrophysics, Pennsylvania State University, University Park, PA 16802, USA',
    },
    'Penn-State-Physics': {
        'cite': 'Dept. of Physics, Pennsylvania State University, University Park, PA 16802, USA',
    },
    'Rochester': {
        'cite': 'Dept. of Physics and Astronomy, University of Rochester, Rochester, NY 14627, USA',
    },
    'SD-Mines-Tech': {
        'cite': 'Physics Department, South Dakota School of Mines and Technology, Rapid City, SD 57701, USA',
    },
    'SNOLAB': {
        'cite': 'SNOLAB, 1039 Regional Road 24, Creighton Mine 9, Lively, ON, Canada P3Y 1N2',
    },
    'Southern': {
        'cite': 'Dept. of Physics, Southern University, Baton Rouge, LA 70813, USA',
    },
    'Stockholm': {
        'cite': 'Oskar Klein Centre and Dept. of Physics, Stockholm University, SE-10691 Stockholm, Sweden',
    },
    'Stony-Brook': {
        'cite': 'Dept. of Physics and Astronomy, Stony Brook University, Stony Brook, NY 11794-3800, USA',
    },
    'Sungkyunkwan-Physics': {
        'cite': 'Dept. of Physics, Sungkyunkwan University, Suwon 16419, Korea',
    },
    'Sungkyunkwan-Basic-Science': {
        'cite': 'Institute of Basic Science, Sungkyunkwan University, Suwon 16419, Korea',
    },
    'Texas-Arlington': {
        'cite': 'Dept. of Physics, University of Texas at Arlington, 502 Yates St., Science Hall Rm 108, Box 19059, Arlington, TX 76019, USA',
    },
    'UC-Berkeley': {
        'cite': 'Dept. of Physics, University of California, Berkeley, CA 94720, USA',
    },
    'UC-Irvine': {
        'cite': 'Dept. of Physics and Astronomy, University of California, Irvine, CA 92697, USA',
    },
    'UCLA': {
        'cite': 'Department of Physics and Astronomy, UCLA, Los Angeles, CA 90095, USA',
    },
    'Uppsala': {
        'cite': 'Dept. of Physics and Astronomy, Uppsala University, Box 516, S-75120 Uppsala, Sweden',
    },
    'UW-Madison-Astronomy': {
        'cite': 'Dept. of Astronomy, University of Wisconsin–Madison, Madison, WI 53706, USA',
    },
    'UW-Madison-WIPAC': {
        'cite': 'Dept. of Physics and Wisconsin IceCube Particle Astrophysics Center, University of Wisconsin–Madison, Madison, WI 53706, USA',
    },
    'UW-River-Falls': {
        'cite': 'Dept. of Physics, University of Wisconsin, River Falls, WI 54022, USA',
    },
    'Wuppertal': {
        'cite': 'Dept. of Physics, University of Wuppertal, D-42119 Wuppertal, Germany',
    },
    'Yale': {
        'cite': 'Dept. of Physics, Yale University, New Haven, CT 06520, USA',
    },
}


def main():
    parser = argparse.ArgumentParser(description='IceCube Keycloak setup')
    parser.add_argument('keycloak_url', help='Keycloak url')
    parser.add_argument('user_mgmt_url', help='User Management url')
    parser.add_argument('--keycloak_realm', default='IceCube', help='Keycloak realm')
    parser.add_argument('-u','--username', default='admin', help='admin username')
    parser.add_argument('-p','--password', default='admin', help='admin password')

    args = parser.parse_args()

    os.environ['KEYCLOAK_REALM'] = args.keycloak_realm
    os.environ['KEYCLOAK_URL'] = args.keycloak_url
    os.environ['USERNAME'] = args.username
    os.environ['PASSWORD'] = args.password

    # set up realm and REST API
    secret = bootstrap()
    os.environ['KEYCLOAK_CLIENT_ID'] = 'rest-access'
    os.environ['KEYCLOAK_CLIENT_SECRET'] = secret
    rest_client = get_rest_client()

    # set up basic group structure
    async def create_subgroups(root, values):
        for name in values:
            groupname = root+'/'+name
            await create_group(groupname, rest_client=rest_client)
            if isinstance(values, dict) and values[name]:
                await create_subgroups(groupname, values[name])
    asyncio.run(create_subgroups('', GROUPS))

    # set up institutions
    async def create_insts(base, inst_list):
        for name in inst_list:
            groupname = base+'/'+name
            await create_group(groupname, attrs=inst_list[name], rest_client=rest_client)
            await create_group(groupname+'/_admin', rest_client=rest_client)
            await create_group(groupname+'/authorlist', rest_client=rest_client)
    asyncio.run(create_insts('/institutions/IceCube', ICECUBE_INSTS))

    # set up user_mgmt app
    token = get_token()
    user_mgmt_app(args.user_mgmt_url, token=token)


if __name__ == '__main__':
    main()
