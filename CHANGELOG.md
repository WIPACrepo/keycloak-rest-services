# Changelog

<!--next-version-placeholder-->

## v1.4.46 (2023-11-08)

### Other

* Introduce special value "none" for institutions_last_seen ([#115](https://github.com/WIPACrepo/keycloak-rest-services/issues/115)) ([`69339a6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/69339a6f1677142cb75be8dc5361a080807045bb))
* Make local test environment match what we have in github ([#114](https://github.com/WIPACrepo/keycloak-rest-services/issues/114)) ([`b15dd38`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b15dd38c29e089cc6b0444f65055a1ba7e97b0d2))
* Update_institution_tracking: don't assume canonical_email is defined ([#113](https://github.com/WIPACrepo/keycloak-rest-services/issues/113)) ([`cded189`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cded189577ebfafc98b86b27919e7651d72a972a))

## v1.4.45 (2023-10-23)

### Other

* <bot> update dependencies*.log files(s) ([`8124e12`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8124e12d3b406526f77991dde087e41a94da3c95))
* Gmail support ([#112](https://github.com/WIPACrepo/keycloak-rest-services/issues/112)) ([`6661fe3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6661fe3ef2d200f095b2f3da3956a3b2d62316fb))

## v1.4.44 (2023-10-12)

### Other

* Py 3.12 support ([#111](https://github.com/WIPACrepo/keycloak-rest-services/issues/111)) ([`aa54825`](https://github.com/WIPACrepo/keycloak-rest-services/commit/aa54825d6c9398e3e3cab478be4c9436a6aebbee))

## v1.4.43 (2023-10-10)

### Other

* Implement force_creation_in_gws custom user attribute ([#109](https://github.com/WIPACrepo/keycloak-rest-services/issues/109)) ([`e980721`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e9807218db3a54c0d17f36451079d3184d1c4018))

## v1.4.42 (2023-10-04)

### Other

* Fix create_posix_user re-enable ([#108](https://github.com/WIPACrepo/keycloak-rest-services/issues/108)) ([`a0804bb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a0804bbde5550ebd368e4b5a9ae7d7e31f41bff8))

## v1.4.41 (2023-10-02)

### Other

* Use `WIPACrepo/wipac-dev-py-setup-action@v2.6` ([#107](https://github.com/WIPACrepo/keycloak-rest-services/issues/107)) ([`ea1f305`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ea1f3059b0ecde98c67db9bba6f8f80befffcdde))
* <bot> update setup.cfg ([`af94327`](https://github.com/WIPACrepo/keycloak-rest-services/commit/af943271ad91d427e3339720e2095bc862afe62d))
* Wipac_cicd.yaml: revert wipac-dev-py-setup-action to 1.14 ([`321524d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/321524df20cc9a67ce4195b9379bbaf0cb99abd3))
* <bot> update dependencies*.log files(s) ([`8ed111f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8ed111f4545e80e2fe2ff97ae215ddb28af0e249))

## v1.4.40 (2023-10-02)

### Other

* <bot> update dependencies*.log files(s) ([`81c9389`](https://github.com/WIPACrepo/keycloak-rest-services/commit/81c9389343b3b3b82b37fa83fbeee859fbf6629f))

## v1.4.39 (2023-10-02)

### Other

* <bot> update dependencies*.log files(s) ([`c0dea7f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c0dea7f7a414fd54c96abd7f555fa34b953e216e))

## v1.4.38 (2023-10-02)

### Other

* Actions/sync_gws_mailing_lists.py: sanitize preferred emails ([#106](https://github.com/WIPACrepo/keycloak-rest-services/issues/106)) ([`ec69c35`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ec69c354989c043855db38db1303089a06d4f7a3))

## v1.4.37 (2023-08-14)

### Other

* Actions/sync_gws_mailing_lists.py: update documentation ([`1d93e69`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1d93e69b996df80bf113d464b2057f6e619778f6))

## v1.4.36 (2023-08-14)

### Other

* Move unidecode to a full dependency ([#105](https://github.com/WIPACrepo/keycloak-rest-services/issues/105)) ([`adcbee4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/adcbee4b242ca661114baddbdb3f57b05372d00e))

## v1.4.35 (2023-08-11)

### Other

* Actions/sync_gws_accounts.py reduce alias retry logging ([#104](https://github.com/WIPACrepo/keycloak-rest-services/issues/104)) ([`684ff83`](https://github.com/WIPACrepo/keycloak-rest-services/commit/684ff83790ae29f2cf101aa6355986a18b83ca78))

## v1.4.34 (2023-08-10)

### Other

* Fix logging bug in actions/track_user_institutions.py ([#103](https://github.com/WIPACrepo/keycloak-rest-services/issues/103)) ([`26701a0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/26701a0bb57f29f99af3fbfd95cad6a349783a5c))
* Actions/sync_gws_accounts.py: be more careful with HttpError ([`1109a4a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1109a4ac9842f3ea2153cec5dd258b58717b985d))

## v1.4.33 (2023-08-10)

### Other

* Actions/sync_gws_accounts.py: implement a more aggressive back-off ([`d6d1ca6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d6d1ca6af454e5f8be8a8fc3018decc98c55a2ce))

## v1.4.32 (2023-08-09)

### Other

* Deprovision_mailing_lists.py: deprovision _admin subgroup too ([#102](https://github.com/WIPACrepo/keycloak-rest-services/issues/102)) ([`c3751e8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c3751e819a58d0a4ac9b95d9834402078a58e952))

## v1.4.31 (2023-08-09)

### Other

* Actions/track_user_institutions.py: notify institutionless users ([#101](https://github.com/WIPACrepo/keycloak-rest-services/issues/101)) ([`3c41046`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3c41046ec019a7c7a10656cfd7a3e25cffd9113a))

## v1.4.30 (2023-08-08)

### Other

* <bot> update requirements.txt ([`e97ee0c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e97ee0c74fba3d0993e4a2a9472956964cd5e735))
* <bot> update requirements.txt ([`29dcc19`](https://github.com/WIPACrepo/keycloak-rest-services/commit/29dcc194c30a9a71319142b7eae7a74a569f76c1))
* <bot> update requirements.txt ([`ff3cfc9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ff3cfc973301f406703bc7d71f62de844fcae1c3))
* <bot> update requirements-tests.txt ([`4115bee`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4115bee7e71a2125cff00cba1781266d9f0c5992))
* <bot> update requirements-actions.txt ([`71a0b57`](https://github.com/WIPACrepo/keycloak-rest-services/commit/71a0b5792f4bb27a3205f104ce21f4075a3b5c7b))
* <bot> update requirements.txt ([`1936b18`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1936b185e89c875b9598e3a3cb8a9751aa7b3345))
* <bot> update requirements-tests.txt ([`5ad974d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5ad974d9b8b45a96d1ae35747cfb1344895abd07))
* <bot> update requirements-actions.txt ([`6ca2bc3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6ca2bc3b1008c5dfaf345f983fa3a88afca5fcfb))
* <bot> update requirements.txt ([`1d76e4e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1d76e4e22d82cc3a2f726c876eca6f858b974576))
* <bot> update requirements-tests.txt ([`d094e9e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d094e9eff5cd75f41ff1e0dc8ee2de572bf54b4f))
* <bot> update requirements-actions.txt ([`4abce35`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4abce35a764797fe122574751eb911c034ad9e9e))

## v1.4.29 (2023-08-08)

### Other

* Actions/sync_gws_accounts.py: be more persistent when creating aliases ([#100](https://github.com/WIPACrepo/keycloak-rest-services/issues/100)) ([`9fd5c9e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9fd5c9ed090b032d93dd9bf228880c92566c8f5b))

## v1.4.28 (2023-08-07)

### Other

* Ignore mailing_list_email attr if it's an IceCube address ([#99](https://github.com/WIPACrepo/keycloak-rest-services/issues/99)) ([`40bff7d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/40bff7df5fde1aa8aa79b2ceb0d9680f44df0b94))

## v1.4.27 (2023-08-07)

### Other

* Actions/util.py: set SSH loglevel to ERROR ([#98](https://github.com/WIPACrepo/keycloak-rest-services/issues/98)) ([`1ea8828`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1ea8828ef43a68fadc698b2064e71f0d4ece0733))

## v1.4.26 (2023-08-04)

### Other

* Fix typos in actions/sync_gws_mailing_lists.py ([`78b34c9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/78b34c9e0d42d9a7b0439e10a6052095ff0961d6))

## v1.4.25 (2023-08-04)

### Other

* Improve notifications by sync_gws_mailing_lists.py ([`eb51b30`](https://github.com/WIPACrepo/keycloak-rest-services/commit/eb51b30eecfae48261fa3af0c70f2b324b4c8915))

## v1.4.24 (2023-08-04)

### Other

* Improve text of notifications ([`c0b7856`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c0b785676fb9014051fa0f95800b27b8ee0e516e))

## v1.4.23 (2023-08-04)

### Other

* Deprovision_mailing_lists.py: fix argument list ([#97](https://github.com/WIPACrepo/keycloak-rest-services/issues/97)) ([`ef90c3f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ef90c3f6cb4fb91feee5070f485d98373fe8d2e7))

## v1.4.22 (2023-08-03)

### Other

* Make sync_gws_mailing_lists.py notify users of changes ([#96](https://github.com/WIPACrepo/keycloak-rest-services/issues/96)) ([`7bb5e5c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7bb5e5c38d3bc0c28807665f472a9338ec1353f2))

## v1.4.21 (2023-08-02)

### Other

* Handling mailing_list_email attr in sync_gws_mailing_lists.py ([#94](https://github.com/WIPACrepo/keycloak-rest-services/issues/94)) ([`b2c35fb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b2c35fb8c8a93ecc76ad49293af3f38330ec1c4a))

## v1.4.20 (2023-08-02)

### Other

* Use python 3.9 ([#95](https://github.com/WIPACrepo/keycloak-rest-services/issues/95)) ([`3dfd81a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3dfd81ab9166ac1d68b657c4ea9953d1e531299a))

## v1.4.19 (2023-07-31)

### Other

* Make get_group_membership raise GroupDoesNotExist instead of KeyError ([#93](https://github.com/WIPACrepo/keycloak-rest-services/issues/93)) ([`254b376`](https://github.com/WIPACrepo/keycloak-rest-services/commit/254b3760e7ac7fa16bd85bbf9eeb85b58243f9e8))

## v1.4.18 (2023-07-26)

### Other

* <bot> update requirements.txt ([`e48d781`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e48d781b5818757b172847b3f2fbe5e6f2c32738))
* <bot> update requirements-tests.txt ([`f055d4a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f055d4a1347a238eaf1d77bd038c619bb6412a6a))
* <bot> update requirements-actions.txt ([`0e4a013`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0e4a0131fb34a7b8b0c4eb867d55237778395d17))
* Tweak log levels in sync_gws_mailing_lists ([`aec4d30`](https://github.com/WIPACrepo/keycloak-rest-services/commit/aec4d309ec7e674451e6207e5cca800643c4a23a))

## v1.4.17 (2023-07-25)

### Other

* Add "group does not exist" exception ([#92](https://github.com/WIPACrepo/keycloak-rest-services/issues/92)) ([`a996550`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a996550b57fd5c448325471aaa5de41752523271))

## v1.4.16 (2023-07-25)

### Other

* Better handle missing 'email' attr in sync_gws_mailing_lists ([`ea9c41a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ea9c41adf39795351b1d7efcf5c644a29378dc3d))
* Make group_info_by_id recursively flatten attribute values ([#91](https://github.com/WIPACrepo/keycloak-rest-services/issues/91)) ([`3f4a83d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3f4a83d1a250f6a7fd2801dd606f22e1595f90de))

## v1.4.15 (2023-07-25)

### Other

* Clarify function of krs.group --new-group-path cli option ([#88](https://github.com/WIPACrepo/keycloak-rest-services/issues/88)) ([`77442a0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/77442a0cddea53281a7cd0be60b6da0f9c73853e))

## v1.4.14 (2023-07-25)

### Other

* <bot> update requirements-actions.txt ([`73036fd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/73036fd95c3c83c91693e0e2fa1a97dbcb580c5d))
* Add unsubscription notification to deprovision_mailing_lists ([#87](https://github.com/WIPACrepo/keycloak-rest-services/issues/87)) ([`bd30ce4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bd30ce48d41cbec61a70e4be312286727343ba5f))

## v1.4.13 (2023-07-24)

### Other

* Handle empty 'email' attr in sync_gws_mailing_lists ([`04eee85`](https://github.com/WIPACrepo/keycloak-rest-services/commit/04eee859fb8cac473b88c66468db7793b636c812))

## v1.4.12 (2023-07-24)

### Other

* Better handle missing 'email' attr in sync_gws_mailing_lists ([`b933136`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b933136be9ccdf90eed565ebd10ac40035f17561))

## v1.4.11 (2023-07-24)

### Other

* Fix typo ([`f6b7fcd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f6b7fcd2b0238a845166e9d009afdd515c39f887))
* Handle missing allow_members_from_experiments in deprovision_mailing_… ([#89](https://github.com/WIPACrepo/keycloak-rest-services/issues/89)) ([`21e3078`](https://github.com/WIPACrepo/keycloak-rest-services/commit/21e307813a47a68e52088b5886d1f7aace829c17))

## v1.4.10 (2023-07-21)

### Other

* Support for modifying group attributes from command line ([#86](https://github.com/WIPACrepo/keycloak-rest-services/issues/86)) ([`2809902`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2809902d74b9e89d88684034b951a90dd1bb7eee))

## v1.4.9 (2023-07-19)

### Other

* Make sync_gws_mailing_lists support group member roles ([#85](https://github.com/WIPACrepo/keycloak-rest-services/issues/85)) ([`cd38c3d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cd38c3de1eec524f06244661e2d89579f1d28c48))

## v1.4.8 (2023-07-17)

### Other

* Add sync_gws_mailing_lists action ([#84](https://github.com/WIPACrepo/keycloak-rest-services/issues/84)) ([`02a37ea`](https://github.com/WIPACrepo/keycloak-rest-services/commit/02a37eab1000a105cc5dd027711db85c79167ef4))

## v1.4.7 (2023-07-17)

### Other

* Pin semantic release to old version that worked ([`5aa2595`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5aa259539ae1d08fc1d5929c4c8f6e1fd813a6c8))
* Talk to old servers via ssh-rsa, like i3mail ([#83](https://github.com/WIPACrepo/keycloak-rest-services/issues/83)) ([`d1da17a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d1da17af6f7d18e5bbdd8b4392c1d9af7f0ac2fb))

## v1.4.6 (2023-07-13)

### Other

* Add deprovision_mailing_lists action ([#82](https://github.com/WIPACrepo/keycloak-rest-services/issues/82)) ([`3a10436`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3a10436674fed7c6edcdf41fce30e40222ac545a))

## v1.4.5 (2023-07-13)

### Other

* Delete update_institutionless_users action ([`88dd2d8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/88dd2d8cebf08ff94f8efb784ebf8f9871fe8f87))

## v1.4.4 (2023-07-13)

### Other

* <bot> update requirements.txt ([`62b572e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/62b572e9c338cec9f74b0367e083b61b244f0a7d))
* <bot> update requirements-tests.txt ([`2418a6a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2418a6a9d54ed944823807832648b74915dab432))
* <bot> update requirements-actions.txt ([`b210347`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b21034725c8f4eb7ea96ec3682dd0cf61aa51f65))
* Rename update_user_institutions to track_user_institutions ([`f0cb56b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f0cb56be4864663dd8a210268fcbc1369425f797))

## v1.4.3 (2023-07-12)

### Other

* Add action to track users' institutions ([#81](https://github.com/WIPACrepo/keycloak-rest-services/issues/81)) ([`7572b5b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7572b5be610576589af9ae5f30168f7ebb228da2))

## v1.4.2 (2023-07-11)

### Other

* Try testing list user attrs ([#80](https://github.com/WIPACrepo/keycloak-rest-services/issues/80)) ([`d18c06b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d18c06bb8e6d807f7245b3b3a4389e5e09ac93d8))

## v1.4.1 (2023-07-07)

### Other

* Add action to manage institutionless_since attribute ([#78](https://github.com/WIPACrepo/keycloak-rest-services/issues/78)) ([`565474e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/565474e8c84fb64ca9e438ee9f44b0e69580338f))

## v1.4.0 (2023-05-31)


## v1.3.10 (2023-05-24)
### Other
* Bump py-versions CI release v2.1 ([#76](https://github.com/WIPACrepo/keycloak-rest-services/issues/76)) ([`4951345`](https://github.com/WIPACrepo/keycloak-rest-services/commit/49513458dc5a4a1e24369880136bddcaa5dee415))

## v1.3.9 (2023-05-05)
### Other
* Add canonical_email alias when creating new google workspace accounts ([#72](https://github.com/WIPACrepo/keycloak-rest-services/issues/72)) ([`9d48eb9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9d48eb9a6589115cad7cfa5ec154475d479f1adf))

## v1.3.8 (2023-05-01)
### Other
* Implement canonical_email user attribute ([`088cf94`](https://github.com/WIPACrepo/keycloak-rest-services/commit/088cf9446f5fb555bc08a8a404eedc03f1954400))

## v1.3.7 (2023-04-20)
### Other
* Remove extra pyjwt dep, since it gets pulled in through wipac-rest-tools ([#70](https://github.com/WIPACrepo/keycloak-rest-services/issues/70)) ([`fc0a6ad`](https://github.com/WIPACrepo/keycloak-rest-services/commit/fc0a6ad9004af23f1a1a5015cb77df3ec4769edf))

## v1.3.6 (2023-02-22)


## v1.3.5 (2023-02-14)


## v1.3.4 (2023-02-09)


## v1.3.3 (2022-11-01)


## v1.3.2 (2022-10-26)


## v1.3.1 (2022-10-25)


## v1.3.0 (2022-08-16)
### Feature
* Fix QUOTAS dict to use 'username' for ceph quota paths ([#60](https://github.com/WIPACrepo/keycloak-rest-services/issues/60)) ([`3b3b355`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3b3b35557e9cea3b8b4bb8c61a1ae038c2bc3ce8))

## v1.2.10 (2022-08-15)


## v1.2.9 (2022-08-15)


## v1.2.8 (2022-08-15)


## v1.2.7 (2022-08-12)


## v1.2.6 (2022-06-24)


## v1.2.5 (2022-06-24)


## v1.2.4 (2022-06-24)


## v1.2.3 (2022-06-24)


## v1.2.2 (2022-06-24)


## v1.2.1 (2022-05-12)


## v1.2.0 (2022-04-04)
### Feature
* Flake8 fixes ([#53](https://github.com/WIPACrepo/keycloak-rest-services/issues/53)) ([`02548ed`](https://github.com/WIPACrepo/keycloak-rest-services/commit/02548ed28b4add44d5625441c56983a6a838afe4))

## v1.1.18 (2022-04-04)


## v1.1.17 (2022-04-04)


## v1.1.16 (2022-03-04)


## v1.1.15 (2022-02-21)


## v1.1.14 (2021-12-28)


## v1.1.13 (2021-12-28)


## v1.1.12 (2021-12-28)


## v1.1.11 (2021-12-28)


## v1.1.10 (2021-12-21)


## v1.1.9 (2021-12-20)


## v1.1.8 (2021-12-16)


## v1.1.7 (2021-12-15)


## v1.1.6 (2021-12-10)


## v1.1.5 (2021-12-10)


## v1.1.4 (2021-12-08)


## v1.1.3 (2021-12-08)


## v1.1.2 (2021-12-08)


## v1.1.1 (2021-12-08)


## v1.1.0 (2021-12-07)
### Feature
* Cleanups for action scripts to match historical usage. ready for prod. ([`ecf230c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ecf230cd99a0ed909781a86a0898075507d71d12))

## v1.0.56 (2021-12-07)


## v1.0.55 (2021-12-05)


## v1.0.54 (2021-12-05)


## v1.0.53 (2021-12-05)


## v1.0.52 (2021-12-05)


## v1.0.51 (2021-12-05)


## v1.0.50 (2021-12-04)


## v1.0.49 (2021-12-04)


## v1.0.48 (2021-12-03)


## v1.0.47 (2021-12-03)


## v1.0.46 (2021-12-03)


## v1.0.45 (2021-12-03)


## v1.0.44 (2021-12-03)


## v1.0.43 (2021-12-03)


## v1.0.42 (2021-11-30)


## v1.0.41 (2021-11-30)


## v1.0.40 (2021-11-29)


## v1.0.39 (2021-11-12)


## v1.0.38 (2021-11-12)


## v1.0.37 (2021-11-11)


## v1.0.36 (2021-11-09)


## v1.0.35 (2021-11-09)


## v1.0.34 (2021-11-08)


## v1.0.33 (2021-11-05)


## v1.0.32 (2021-11-05)


## v1.0.31 (2021-11-05)


## v1.0.30 (2021-11-05)


## v1.0.29 (2021-11-05)


## v1.0.28 (2021-11-05)


## v1.0.27 (2021-11-05)


## v1.0.26 (2021-11-05)


## v1.0.25 (2021-11-05)


## v1.0.24 (2021-11-05)


## v1.0.23 (2021-11-05)


## v1.0.22 (2021-11-05)


## v1.0.21 (2021-11-04)


## v1.0.20 (2021-11-02)


## v1.0.19 (2021-11-02)


## v1.0.18 (2021-11-02)


## v1.0.17 (2021-11-02)


## v1.0.16 (2021-11-01)


## v1.0.15 (2021-10-21)


## v1.0.14 (2021-10-19)


## v1.0.13 (2021-10-19)


## v1.0.12 (2021-10-19)


## v1.0.11 (2021-10-19)


## v1.0.10 (2021-10-19)


## v1.0.9 (2021-10-15)


## v1.0.8 (2021-09-23)


## v1.0.7 (2021-08-18)


## v1.0.6 (2021-08-05)


## v1.0.5 (2021-08-04)


## v1.0.4 (2021-07-30)


## v1.0.3 (2021-04-19)


## v1.0.2 (2021-03-25)


## v1.0.1 (2021-03-25)

