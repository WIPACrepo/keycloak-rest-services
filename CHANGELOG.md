# CHANGELOG



## v1.4.123 (2025-06-05)

###  

* fix getattr error (#176) ([`d6fa407`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d6fa4072c2d2faea8de3e86740d5248d13ec243d))


## v1.4.122 (2025-06-05)

###  

* allow specifying TLS settings for the ldap connection (#175)

* allow specifying TLS settings for the ldap connection

* &lt;bot&gt; update dependencies*.log files(s)

* remove dup argument

* catch error better

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`2cc285b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2cc285b7e28b66b5e314dac1e852246f0d42b9c2))


## v1.4.121 (2025-05-29)

###  

* custom jar to hold script mappers (#174)

* custom jar to hold script mappers

* &lt;bot&gt; update dependencies*.log files(s)

* a working version of the scitokens mapper

* &lt;bot&gt; update dependencies*.log files(s)

* add readme for custom jars

* remove built jars

* &lt;bot&gt; update dependencies*.log files(s)

* fix FROM/AS casing error

* build custom jars for keycloak image build in CI

* add jar back to git. it&#39;s just easier this way

* bump ci versions for docker actions

* empty search no longer does the right thing in 26.2

* &lt;bot&gt; update dependencies*.log files(s)

* empty search no longer does the right thing in 26.2. attempt 2

* do same fix for list_insts

* add more docs to mapper header

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`26c4584`](https://github.com/WIPACrepo/keycloak-rest-services/commit/26c4584c4a3743a66663266a4eb63bc4362b999a))


## v1.4.120 (2025-04-15)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`e8c9d1b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e8c9d1b2cf57fde34163a5f69f5c6f94e71e45c8))

* Use `pypa/gh-action-pypi-publish@v1.12.4` ([`1dd781a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1dd781a4318682f50775a8706b79749359ba19eb))


## v1.4.119 (2025-03-04)

###  

* Re-enable the Testing Image&#39;s TLS Cert (#173) ([`d124c58`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d124c589e89c7298ea508b014d7f3d22ee61747f))


## v1.4.118 (2025-02-20)

###  

* Update GHA Workflow - 3 ([`48ea93b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/48ea93b9b5b65ee3ae11fa37d0c78f86a8ed12d5))

* Update GHA Workflow - 2 (#171) ([`839af3c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/839af3cdd1225a749d2267332576936c217c066a))

* Update GHA Workflow (Use `pyproject.toml`) (#170)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`e9200bf`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e9200bfcf12390e7e6b1d3ed5e9699007deff3f3))


## v1.4.117 (2024-12-06)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`56c9cde`](https://github.com/WIPACrepo/keycloak-rest-services/commit/56c9cde47f6db6a648c0e0ecb9271205cddd5776))

* krs/users.py: fix argument parsing bug ([`b0c568a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b0c568a990f9179bd5b74215c79ff9d8d53d1894))


## v1.4.116 (2024-12-04)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`ca4091b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ca4091b56b9550cb21783429cc86bbce54e4c950))

* start using keycloak:26.0.7 for testing ([`c6a529c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c6a529ccaf8d07539f629967fd814761bdd13a2f))


## v1.4.115 (2024-11-27)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`9ee5e57`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9ee5e57119afc1ac5fe4120d254e2927c44e6144))

* remove pre-v24 compatibility code (#168)

This was necessary only during the upgrade to v24

* add test for /groups returning empty subgroups

* &lt;bot&gt; update dependencies*.log files(s)

* remove pre-v24 compatibility code

* make flake8 happy

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`c630de7`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c630de742d84ed7d3e7b9860ab9d3d38cc85cba0))


## v1.4.114 (2024-11-25)

###  

* keycloak 26.0.6 compatibility (#167)

* switch to keycloak 26.0.6

* &lt;bot&gt; update dependencies*.log files(s)

* update list_users query handling for 26.0.6

* make flake8 happy

* comment update

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`2a84a46`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2a84a4628fbfd17484eed70ec89d4f283599ae41))


## v1.4.113 (2024-11-21)

###  

* update keycloak theme (#166)

* update keycloak theme

* use custom theme in keycloak container

* copy keycloak_theme to the container ([`7eaedfa`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7eaedfae11e09068d61836a8464829528fd7300c))


## v1.4.112 (2024-11-21)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`85da40b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/85da40b4c637e262c78f5948d8d9c8b3ac2df087))

* add scope &#34;basic&#34; to user_mgmt_app() (#165)

* add scope &#34;basic&#34; to user_mgmt_app()

Keycloak 25.0.0 introduced the change described below that caused
user_mgmt unit tests to fail authentication because keycloak would
send tokens without the &#39;sub&#39; claim. This patch to user_mgmt_app()
should fix that.

NEW DEFAULT CLIENT SCOPE BASIC
The new client scope named basic is added as a realm &#34;default&#34; client scope
and hence will be added to all newly created OIDC clients. The client scope
is also automatically added to all existing OIDC clients during migration.

This scope contains preconfigured protocol mappers for the following claims:
* sub (See the details below in the dedicated section)
* auth_tim

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`bd896f5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bd896f570a65b950a724403f0a00ccf8ef7d91b2))


## v1.4.111 (2024-11-19)

###  

* use a form of datetime.now() that works with more versions of python ([`3883969`](https://github.com/WIPACrepo/keycloak-rest-services/commit/388396943d28919a6504d91c0ed6b71c8a724acf))

* address datetime.utcnow deprecation ([`8cd889e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8cd889e0c934d54d94ea203cacfc7c5749542ac7))


## v1.4.110 (2024-11-19)

###  

* keycloak 26 docker upgrades (#164)

* keycloak 26 docker upgrades

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`2547f3a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2547f3a7d0db2948a6376296a980c9c1103c6d3a))


## v1.4.109 (2024-10-17)

###  

* delete actions/create_email_account.py (#163)

* delete actions/create_email_account.py (No longer needed)

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`0c56756`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0c5675679674b4f896e6bdb58f1912eb57cecf6c))


## v1.4.108 (2024-08-01)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`b2a7078`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b2a7078669d394756bb2d94fcb860d561d12a6e7))

* Generate unique canonical emails (#161)

* dependencies-from-Dockerfile.log

* add attribute query capability to krs.users.list_users

* generate unique canonical addrs when creating users

* keep pycharm happy ([`374fcad`](https://github.com/WIPACrepo/keycloak-rest-services/commit/374fcada2c0bb91ce209cbcbb9a32f6648f1d0ab))


## v1.4.107 (2024-07-10)

###  

* reduce prune_mail_groups_by_experiment logging noise (#158)

* reduce prune_mail_groups_by_experiment logging noise

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`bc82613`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bc82613021b2b89baf55ac38c28f5e21fb4b54a2))


## v1.4.106 (2024-06-28)

###  

* tiny tweaks to actions/sync_gws_calendars.py (#157) ([`d7f08d9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d7f08d944b7eaef6f4404d2f9eb528d9fa48951c))


## v1.4.105 (2024-06-27)

###  

* add actions/sync_gws_calendars.py ([`e034067`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e03406714acf3b9b94c8622d699f0877a9d48a3f))


## v1.4.104 (2024-06-19)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`76bb5af`](https://github.com/WIPACrepo/keycloak-rest-services/commit/76bb5afdea01a2ce5d80abab9facfd4093fc72ac))

* actions/track_user_institutions.py: small improvement ([`0f4827a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0f4827a086f34a3054a31eed9ae9914d442e0615))

* actions/track_user_institutions.py: flake8 fix ([`25b6234`](https://github.com/WIPACrepo/keycloak-rest-services/commit/25b6234a8e708d2554dd83a49a8f61f58229bb29))

* actions/track_user_institutions.py: notify on all changes ([`aac0d63`](https://github.com/WIPACrepo/keycloak-rest-services/commit/aac0d632a11492f2ce3825dc92b58d202c5d9a3b))


## v1.4.103 (2024-06-19)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`f49c535`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f49c535b6d5f30f212580f82ec2612fa4fd6c1e7))

* actions/track_user_institutions.py: handle HTTP 400 ([`a0cb90c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a0cb90c21315f854b81e58ef2ccb2cd6ee3e70a4))


## v1.4.102 (2024-06-18)

###  

* update group member email script to allow globs, multiple emails ([`cb0298d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cb0298dd95ab5151d934bf85f9f58337dcdfb4e8))


## v1.4.101 (2024-06-18)

###  

* sync_gws_mailing_lists: add more logging ([`e1abba2`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e1abba2b4a4df7c426acb4e18d5b44fb601811dd))


## v1.4.100 (2024-06-18)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`8b860ab`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8b860abc5c086d8b963cc9bd8b3e914af67b0b95))

* sync_gws_mailing_lists: normalize address case ([`62417dc`](https://github.com/WIPACrepo/keycloak-rest-services/commit/62417dc83a4ec8365991d17e78c8d44767d94b11))


## v1.4.99 (2024-06-13)

###  

* docstring update ([`9ad2212`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9ad22125b6c876f29f680e61cefa993b2c6e6586))


## v1.4.98 (2024-06-13)

###  

* make help less confusing ([`248ad90`](https://github.com/WIPACrepo/keycloak-rest-services/commit/248ad90cde3547102b3c8be8bd9ba1f18356a46e))


## v1.4.97 (2024-06-13)

###  

* more tweaks to action logging ([`a7665f7`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a7665f75d980b889b67d6d4867704692c36a7805))


## v1.4.96 (2024-06-12)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`893de70`](https://github.com/WIPACrepo/keycloak-rest-services/commit/893de702456e1487aeb252eb6d7d90e300ec09a2))

* tweak logging levels ([`c54acc3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c54acc3a4d1ddf3d672f48342fb3a350dd658733))


## v1.4.95 (2024-05-31)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`697d460`](https://github.com/WIPACrepo/keycloak-rest-services/commit/697d460eb577d456cec93010123bd4a3db9f17f5))

* track_user_institutions.py: handle missing email ([`7e44fcd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7e44fcd31650e5d3dc14ceb53e40b6d14016b1f7))


## v1.4.94 (2024-05-28)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`dc5c05f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/dc5c05f59da5183f645aaba9d26d257a041628c7))

* minor fixes ([`e9ebda4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e9ebda49cbb899aee70c072ecdccc8111a1170d2))


## v1.4.93 (2024-05-24)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`70e1fdd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/70e1fddde01a837fb273216e22af64051bb99a9f))

* sync_synchronized_groups.py (#152) ([`181d38b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/181d38beff430b08b1a79933c5e9bda09500e2d4))


## v1.4.92 (2024-05-22)

###  

* sync_gws_mailing_lists.py: change group skipping mechanism (#155) ([`eef1a73`](https://github.com/WIPACrepo/keycloak-rest-services/commit/eef1a73be0fda05298ae89b4f9bde707aa2b68f4))


## v1.4.91 (2024-05-22)

###  

* actions/sync_gws_mailing_lists.py: support for automation_blocklist (#154) ([`79833da`](https://github.com/WIPACrepo/keycloak-rest-services/commit/79833dafb9d72d5af80fd68955694c282c0fac51))


## v1.4.90 (2024-05-22)

###  

* Recursive mail list sync tweaks (#153) ([`cf625c5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cf625c56b1a83cdfb12f4491a84ab22c9de5750d))


## v1.4.89 (2024-05-10)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`7fb8acb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7fb8acb3090104babca214bbc6dfab4d9a52e995))

* password expired email: update URL for new keycloak version ([`5c7abc0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5c7abc044da014208398f0e07710dc714d655826))


## v1.4.88 (2024-05-06)

###  

* add krs.groups.get_group_hierarchy (#151) ([`ec96a7c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ec96a7cbd9410119417c301c063b7a31ed6f51e4))


## v1.4.87 (2024-05-06)

###  

* have krs.groups.list_groups include attributes (#150) ([`26c87f0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/26c87f04e7436de3ff2e5c5e1519f35872e7a2e3))


## v1.4.86 (2024-05-02)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`f343a1e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f343a1ef649aab74fb2a8f88abde268b2c349e79))

* Dockerfile back to python 3.10 from 3.11 (it wasn&#39;t the problem)

Python version was unrelated to the problem I was trying to solve.
3.10 is consistent with other tools that use KRS ([`1c9346d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1c9346dbae3b5850ff974ad02e5aace9be94b05a))


## v1.4.85 (2024-05-02)

###  

* fix issue with pagination in list_users with keycloak 23 (#149) ([`aa0de1f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/aa0de1f01054ce635418ed59b4bc3f04a850c16c))


## v1.4.84 (2024-05-01)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`3793ebf`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3793ebfaa24515cf80638bb1506bd5b0ff44476b))

* update python version to 3.11 ([`638b97c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/638b97c7860785560c25798c2b22e1ac375dd792))


## v1.4.83 (2024-05-01)

###  

* remove actions/sync_authors_mail_group.py ([`694937c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/694937cc7c5bd456cca9b44a773e760c88fa9801))

* add sync_group_membership.py action (#148) ([`4e9aa20`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4e9aa20e2e23daead130f0763f2ad146e15d0168))


## v1.4.82 (2024-04-29)

###  

* fix non-determinism in tests ([`d231f35`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d231f35bfce00f3389588ec0df0574cbc7cdec3f))


## v1.4.81 (2024-04-29)

###  

* fix tests/actions/sync_gws_mailing_lists.py (#146) ([`7c01189`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7c01189cdfc9cf258d9992b4c9f2ac6a51a182aa))

* make sync_gws_mailing_lists.py act recursively (#145)

* make sync_gws_mailing_lists.py act recursively ([`d62439d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d62439d56af395f77d31d5308b1983e8c249c564))


## v1.4.80 (2024-04-25)

###  

* make prune_mail_groups_by_experiment.py act recursively (#144)

* make prune_mail_groups_by_experiment.py act recursively ([`639b9fe`](https://github.com/WIPACrepo/keycloak-rest-services/commit/639b9fed0dd20013b6175c4587b947a3dbfaa0f7))


## v1.4.79 (2024-04-24)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`44230dd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/44230ddef1c06add1436cdd365790c93b0b3a4e5))

* add script to look up group member emails ([`5299837`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5299837712ff209d1ae3a9d203debe28f138bc7f))


## v1.4.78 (2024-04-23)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`a9c6c6d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a9c6c6dab4271d2ba1821853d4472c529b310069))

* sync_authors_mail_group.py: doc fixes ([`cf13936`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cf139364e6b8a9b4fc802b8a4e7d82f53d872c5e))


## v1.4.77 (2024-04-22)

###  

* actions/sync_authors_mail_group.py: parametrize experiment name (#143)

* actions/sync_authors_mail_group.py: parametrize experiment name ([`399ffb9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/399ffb9ce1200b978b559a183ae37388b0c61745))


## v1.4.76 (2024-04-17)

###  

* Update README.md ([`ae6b2a1`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ae6b2a1387e5e0770f16a0e1a8b7d82f69ef0f65))


## v1.4.75 (2024-04-17)

###  

* remove uid/gid from email relay creation (#142)

* gmail doesn&#39;t need posix access, so remove that requirement for relay emails

* fix tests

* update to new dependency tracking

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`4fef8a0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4fef8a04c5e30773bf954ce98884d698da5cfb8c))


## v1.4.74 (2024-04-16)

###  

* use keycloak 24.0.3 container ([`3312a8b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3312a8bb8221c0e256dbc246b5ef480f5952c844))


## v1.4.73 (2024-04-11)

###  

* revert missing attributes experiment (#141) ([`c6badc1`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c6badc15ec3f81b082ad929d78427487f0e7476b))


## v1.4.72 (2024-04-11)

###  

* bootstrap.py: missing id token attributes experiment (#140)

* bootstrap.py: missing id token attributes

* add test_bootstrap_user_mgmt ([`3fbbf2c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3fbbf2c42112fede49c160d224eba3d835a5d55b))


## v1.4.71 (2024-04-09)

###  

* sync_gws_mailing_lists.py: handle dup owners (#138) ([`efcaaa5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/efcaaa54f8a028ac7e230485e15c1ddf7e004223))


## v1.4.70 (2024-04-08)

###  

* Use keycloak 24.0.2 for testing (#137) ([`430350d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/430350d14058c86150b7dfdec730425b4ce5a189))


## v1.4.69 (2024-04-04)

###  

* add krs.util.keycloak_version() function (#136)

* add keycloak_version() function ([`a464155`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a4641552b5ef5b174e4695cf415690b2d2b02d86))


## v1.4.68 (2024-04-03)

###  

* pre-keycloak-v23 compatibility (#135)

* pre-keycloak-v23 compatibility

* fix

* fix

* fix

* fix ([`b6221f6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b6221f60a5998ee6fe7a70166e25b6da51c25d53))


## v1.4.67 (2024-04-01)

###  

* use wipac-dev-py-setup-action@v3.1 ([`327db94`](https://github.com/WIPACrepo/keycloak-rest-services/commit/327db94064e12331ffa07a70e80462b5d42f5c32))

* sync_gws_mailing_lists.py: better notifications ([`146e337`](https://github.com/WIPACrepo/keycloak-rest-services/commit/146e33780cc4c50515dc7fddbc06c441983db66d))

* improve removal notification email text (#133)

* improve removal notification email text

* fix ([`77c9d39`](https://github.com/WIPACrepo/keycloak-rest-services/commit/77c9d39cb613864a8eb0c4ae96e6b215d367867d))


## v1.4.66 (2024-03-19)

###  

* compatibility with newest keycloak (#132)

* &lt;bot&gt; update dependencies*.log files(s)

* compatibility with latest keycloak version

* &lt;bot&gt; update dependencies*.log files(s)

* oops

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`0dab13f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0dab13fc3cafbd16ad5f32b15005440d5f85d14f))


## v1.4.65 (2024-02-14)

###  

* sync_authors_mail_group.py: use authorlist* groups, not just authorlist (#130)

* sync_authors_mail_group.py: use authorlist* groups, not just authorlist

* update test

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`7a876a6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7a876a6202cec81bab6f7ec4ca47287037b85eee))


## v1.4.64 (2024-02-13)

###  

* sync_gws_mailing_lists.py: fix order of operations (#129)

* sync_gws_mailing_lists.py: fix order of operations

* &lt;bot&gt; update dependencies*.log files(s)

* update notification messages

* spacing

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`ff26c27`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ff26c2723650f22dbff209fd0098beb828b8a19c))


## v1.4.63 (2024-02-12)

###  

* sync_gws_mailing_lists.py: allow username@iwe to be preferred addresses (#128)

* sync_gws_mailing_lists.py: allow username@iwe to be preferred addresses

* fixup

* fixup ([`0d8a4d6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0d8a4d6e51c5b2197c92a2cefd5d24db629a24ed))


## v1.4.62 (2024-02-12)

###  

* make exceptions make more sense in retry_execute() from actions/util.py (#127) ([`f818e44`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f818e4423a4b493ae0378cf0ba92d625ec5a9fdd))


## v1.4.61 (2024-02-12)

###  

* sync_gws_accounts.py: give time to finishing creating dependencies (#126)

* sync_gws_accounts.py: give time to finishing creating dependencies

* &lt;bot&gt; update dependencies*.log files(s)

* prune_mail_groups_by_experiment.py: make logging less verbose

missing allow_members_from_experiments attribute is now normal

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`662b670`](https://github.com/WIPACrepo/keycloak-rest-services/commit/662b670cef794dac7f2493f5d4102733d8198057))


## v1.4.60 (2024-02-01)

###  

* Implement /mail/authors (#123)

* add actions/sync_authors_mail_group.py ([`5631eee`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5631eee512057e53f4c5dd9ebb65ad763a0c5830))


## v1.4.59 (2024-02-01)

###  

* rename prune_mailing_lists_by_experiment (#125)

* rename prune_mailing_lists_by_experiment

* flake8 fix

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`7925910`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7925910f2fc73680b11aaba3f023d162bb41441c))


## v1.4.58 (2024-01-29)

###  

* actions/util.py: handle http 404 in retry_execute() (#124) ([`85e6aa7`](https://github.com/WIPACrepo/keycloak-rest-services/commit/85e6aa7433d27b765c609bf441d1dac76e00d199))


## v1.4.57 (2024-01-25)

###  

* rename deprovision_mailing_lists.py to prune_mailing_lists_by_experim… (#122)

* rename deprovision_mailing_lists.py to prune_mailing_lists_by_experiment.py

* &lt;bot&gt; update dependencies*.log files(s)

* fixup

* tweak comments

* little fix

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`28cc4a6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/28cc4a6d6b8ef84bae608776cfbedab4a619d9ed))


## v1.4.56 (2024-01-23)

###  

* replace --sa-delegator with --sa-subject, which is more accurate ([`e809a3f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e809a3f9a84b13687fbf375dd0febad6067a96b7))


## v1.4.55 (2024-01-23)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`3d8d7d4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3d8d7d4ce58d178a6f71f0c66885de0fcb69b5f0))

* docs update ([`58565bb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/58565bb0a4d438ddf7a4d887a167bcd86af533e2))


## v1.4.54 (2024-01-22)

###  

* sync_gws_accounts.py: handle partial account setup situations (#121)

* sync_gws_accounts.py: handle partial account setup situations

* improvement ([`a1fba78`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a1fba782c0988ef1a3529a857089eaebf8fe7e8f))


## v1.4.53 (2024-01-22)

###  

* utils.py retry_execute: except HTTP 500 and 503 ([`97d7cc4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/97d7cc440b560180f8f7c69d248f08fb58a9c310))


## v1.4.52 (2024-01-22)

###  

* actions/sync_gws_accounts.py: handle more exceptions (#120)

* actions/sync_gws_accounts.py: handle more exceptions

* &lt;bot&gt; update dependencies*.log files(s)

* fix tests

* fix

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`7825317`](https://github.com/WIPACrepo/keycloak-rest-services/commit/78253174c4bade1609235dbccdffd1599fa7867a))


## v1.4.51 (2024-01-04)

###  

* krs/email.py: handle addresses without domain (#119)

* krs/email.py: handle addresses without domain

* better implementation

* add test_send_email_no_domain ([`5b6beba`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5b6beba4f84b888815af227f06a7985ab9d59c6a))


## v1.4.50 (2024-01-04)

###  

* chore: fix keycloak image version for tests (#118)

* fix keycloak image version for tests

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`022b4e5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/022b4e5d46fb5e8e4e75f5cc7d36b1ff7342fe51))


## v1.4.49 (2023-11-08)

###  

* sync_gws_accounts.py: fix logical error ([`6f9a990`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6f9a990f8537726e0f277660fa8adb75c833a4f3))


## v1.4.48 (2023-11-08)

###  

* sync_gws_accounts.py: require force_creation_in_gws to be &#34;true&#34; or absent ([`a060c21`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a060c216bd053bcc968aa5c688f9cef14f14d145))


## v1.4.47 (2023-11-08)

###  

* actions/create_email_account.py: remove pointless relay of alias ([`0f195e2`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0f195e24a38e2c11018d22e500dbc27277265dfa))

* add test_track_user_institutions.py test ([`9065007`](https://github.com/WIPACrepo/keycloak-rest-services/commit/90650078a9f58a2ba932a49cc1674c2d55dbaed1))


## v1.4.46 (2023-11-08)

###  

* introduce special value &#34;none&#34; for institutions_last_seen (#115) ([`69339a6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/69339a6f1677142cb75be8dc5361a080807045bb))

* make local test environment match what we have in github (#114) ([`b15dd38`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b15dd38c29e089cc6b0444f65055a1ba7e97b0d2))

* update_institution_tracking: don&#39;t assume canonical_email is defined (#113) ([`cded189`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cded189577ebfafc98b86b27919e7651d72a972a))


## v1.4.45 (2023-10-23)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`8124e12`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8124e12d3b406526f77991dde087e41a94da3c95))

* Gmail support (#112)

* add gmail support to actions/sync_gws_accounts.py

* add gmail support to actions/create_email_account.py

* &lt;bot&gt; update dependencies*.log files(s)

* actions/create_email_account.py: don&#39;t create user directories

* remove addition of users to enable-gmail@icecube.wisc.edu

* keep flake8 happy

* &lt;bot&gt; update dependencies*.log files(s)

* actions/create_email_account.py: put canonical sender and recipient back

* fix white space

* cleanup

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`6661fe3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6661fe3ef2d200f095b2f3da3956a3b2d62316fb))


## v1.4.44 (2023-10-12)

###  

* py 3.12 support (#111)

* now try py 3.12

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`aa54825`](https://github.com/WIPACrepo/keycloak-rest-services/commit/aa54825d6c9398e3e3cab478be4c9436a6aebbee))


## v1.4.43 (2023-10-10)

###  

* implement force_creation_in_gws custom user attribute (#109)

* implement force_creation_in_gws custom user attribute

* make flake8 happy

* &lt;bot&gt; update dependencies*.log files(s)

* fix typo

* another typo

* add sanity check

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`e980721`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e9807218db3a54c0d17f36451079d3184d1c4018))


## v1.4.42 (2023-10-04)

###  

* fix create_posix_user re-enable (#108)

* move up so both if branches can use `user`

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update dependencies*.log files(s)

* limit python version until wipac-rest-tools has a release

* &lt;bot&gt; update setup.cfg

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`a0804bb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a0804bbde5550ebd368e4b5a9ae7d7e31f41bff8))


## v1.4.41 (2023-10-02)

###  

* Use `WIPACrepo/wipac-dev-py-setup-action@v2.6` (#107)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`ea1f305`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ea1f3059b0ecde98c67db9bba6f8f80befffcdde))

* &lt;bot&gt; update setup.cfg ([`af94327`](https://github.com/WIPACrepo/keycloak-rest-services/commit/af943271ad91d427e3339720e2095bc862afe62d))

* wipac_cicd.yaml: revert wipac-dev-py-setup-action to 1.14

Switching to 2.6 caused release creation in a loop ([`321524d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/321524df20cc9a67ce4195b9379bbaf0cb99abd3))

* &lt;bot&gt; update dependencies*.log files(s) ([`8ed111f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8ed111f4545e80e2fe2ff97ae215ddb28af0e249))


## v1.4.40 (2023-10-02)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`81c9389`](https://github.com/WIPACrepo/keycloak-rest-services/commit/81c9389343b3b3b82b37fa83fbeee859fbf6629f))


## v1.4.39 (2023-10-02)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`c0dea7f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c0dea7f7a414fd54c96abd7f555fa34b953e216e))


## v1.4.38 (2023-10-02)

###  

* actions/sync_gws_mailing_lists.py: sanitize preferred emails (#106)

* actions/sync_gws_mailing_lists.py: sanitize preferred emails

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* update wipac-dev-py-setup-action to 2.6

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update .gitignore

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`ec69c35`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ec69c354989c043855db38db1303089a06d4f7a3))


## v1.4.37 (2023-08-14)

###  

* actions/sync_gws_mailing_lists.py: update documentation ([`1d93e69`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1d93e69b996df80bf113d464b2057f6e619778f6))


## v1.4.36 (2023-08-14)

###  

* move unidecode to a full dependency (#105)

* move unidecode to a full dependency

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`adcbee4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/adcbee4b242ca661114baddbdb3f57b05372d00e))


## v1.4.35 (2023-08-11)

###  

* actions/sync_gws_accounts.py reduce alias retry logging (#104)

* actions/sync_gws_accounts.py reduce alias retry logging

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* make log message consistent

* fix typo

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`684ff83`](https://github.com/WIPACrepo/keycloak-rest-services/commit/684ff83790ae29f2cf101aa6355986a18b83ca78))


## v1.4.34 (2023-08-10)

###  

* fix logging bug in actions/track_user_institutions.py (#103) ([`26701a0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/26701a0bb57f29f99af3fbfd95cad6a349783a5c))

* actions/sync_gws_accounts.py: be more careful with HttpError ([`1109a4a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1109a4ac9842f3ea2153cec5dd258b58717b985d))


## v1.4.33 (2023-08-10)

###  

* actions/sync_gws_accounts.py: implement a more aggressive back-off ([`d6d1ca6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d6d1ca6af454e5f8be8a8fc3018decc98c55a2ce))


## v1.4.32 (2023-08-09)

###  

* deprovision_mailing_lists.py: deprovision _admin subgroup too (#102)

* deprovision_mailing_lists.py: deprovision _admin subgroup too

* add test for _admin deprovisioning ([`c3751e8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c3751e819a58d0a4ac9b95d9834402078a58e952))


## v1.4.31 (2023-08-09)

###  

* actions/track_user_institutions.py: notify institutionless users (#101)

* actions/track_user_institutions.py: notify institutionless users

* &lt;bot&gt; update requirements-actions.txt

* flake8 fix

* improve wording

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* keep pycharm inspection happy

* improve wording

* improve --dryrun help

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`3c41046`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3c41046ec019a7c7a10656cfd7a3e25cffd9113a))


## v1.4.30 (2023-08-08)

###  

* &lt;bot&gt; update requirements.txt ([`e97ee0c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e97ee0c74fba3d0993e4a2a9472956964cd5e735))

* &lt;bot&gt; update requirements.txt ([`29dcc19`](https://github.com/WIPACrepo/keycloak-rest-services/commit/29dcc194c30a9a71319142b7eae7a74a569f76c1))

* &lt;bot&gt; update requirements.txt ([`ff3cfc9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ff3cfc973301f406703bc7d71f62de844fcae1c3))

* &lt;bot&gt; update requirements-tests.txt ([`4115bee`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4115bee7e71a2125cff00cba1781266d9f0c5992))

* &lt;bot&gt; update requirements-actions.txt ([`71a0b57`](https://github.com/WIPACrepo/keycloak-rest-services/commit/71a0b5792f4bb27a3205f104ce21f4075a3b5c7b))

* &lt;bot&gt; update requirements.txt ([`1936b18`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1936b185e89c875b9598e3a3cb8a9751aa7b3345))

* &lt;bot&gt; update requirements-tests.txt ([`5ad974d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5ad974d9b8b45a96d1ae35747cfb1344895abd07))

* &lt;bot&gt; update requirements-actions.txt ([`6ca2bc3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6ca2bc3b1008c5dfaf345f983fa3a88afca5fcfb))

* &lt;bot&gt; update requirements.txt ([`1d76e4e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1d76e4e22d82cc3a2f726c876eca6f858b974576))

* &lt;bot&gt; update requirements-tests.txt ([`d094e9e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d094e9eff5cd75f41ff1e0dc8ee2de572bf54b4f))

* &lt;bot&gt; update requirements-actions.txt ([`4abce35`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4abce35a764797fe122574751eb911c034ad9e9e))


## v1.4.29 (2023-08-08)

###  

* actions/sync_gws_accounts.py: be more persistent when creating aliases (#100) ([`9fd5c9e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9fd5c9ed090b032d93dd9bf228880c92566c8f5b))


## v1.4.28 (2023-08-07)

###  

* ignore mailing_list_email attr if it&#39;s an IceCube address (#99) ([`40bff7d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/40bff7df5fde1aa8aa79b2ceb0d9680f44df0b94))


## v1.4.27 (2023-08-07)

###  

* actions/util.py: set SSH loglevel to ERROR (#98)

* actions/util.py: set SSH loglevel to ERROR

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* improve wording

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`1ea8828`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1ea8828ef43a68fadc698b2064e71f0d4ece0733))


## v1.4.26 (2023-08-04)

###  

* fix typos in actions/sync_gws_mailing_lists.py ([`78b34c9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/78b34c9e0d42d9a7b0439e10a6052095ff0961d6))


## v1.4.25 (2023-08-04)

###  

* improve notifications by sync_gws_mailing_lists.py ([`eb51b30`](https://github.com/WIPACrepo/keycloak-rest-services/commit/eb51b30eecfae48261fa3af0c70f2b324b4c8915))


## v1.4.24 (2023-08-04)

###  

* improve text of notifications ([`c0b7856`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c0b785676fb9014051fa0f95800b27b8ee0e516e))


## v1.4.23 (2023-08-04)

###  

* deprovision_mailing_lists.py: fix argument list (#97)

* deprovision_mailing_lists.py: fix argument list

* fix test ([`ef90c3f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ef90c3f6cb4fb91feee5070f485d98373fe8d2e7))


## v1.4.22 (2023-08-03)

###  

* make sync_gws_mailing_lists.py notify users of changes (#96)

* make sync_gws_mailing_lists.py notify users of changes

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* document SMTP server config

* fixup

* fixup

* fix typo

* actions/deprovision_mailing_lists.py switch to krs.email

* fix docstring

* add single group support to deprovision_mailing_lists.py

* rename only_group to single_group

* fix test

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`7bb5e5c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7bb5e5c38d3bc0c28807665f472a9338ec1353f2))


## v1.4.21 (2023-08-02)

###  

* handling mailing_list_email attr in sync_gws_mailing_lists.py (#94)

* implement handling of mailing_list_email attr in sync_gws_mailing_lists.py

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* update requirements-actions.txt

* &lt;bot&gt; update requirements-actions.txt

* add asyncache cachetools to setup.cfg

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update requirements-actions.txt

* update setup.cfg

* &lt;bot&gt; update requirements-actions.txt

* update test_sync_gws_mailing_lists.py

* use python 3.9

* improve log msg format

* add option to specify which list to sync

* Revert &#34;add option to specify which list to sync&#34;

This reverts commit 330a3d680b052250934d423c13a2e4eed6bed7bc.

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`b2c35fb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b2c35fb8c8a93ecc76ad49293af3f38330ec1c4a))


## v1.4.20 (2023-08-02)

###  

* use python 3.9 (#95)

* use python 3.9

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`3dfd81a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3dfd81ab9166ac1d68b657c4ea9953d1e531299a))


## v1.4.19 (2023-07-31)

###  

* make get_group_membership raise GroupDoesNotExist instead of KeyError (#93)

* make get_group_membership raise GroupDoesNotExist instead of KeyError

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* add message to GroupDoesNotExist

* tighten exception tests

* fix test_invalid_group group

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`254b376`](https://github.com/WIPACrepo/keycloak-rest-services/commit/254b3760e7ac7fa16bd85bbf9eeb85b58243f9e8))


## v1.4.18 (2023-07-26)

###  

* &lt;bot&gt; update requirements.txt ([`e48d781`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e48d781b5818757b172847b3f2fbe5e6f2c32738))

* &lt;bot&gt; update requirements-tests.txt ([`f055d4a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f055d4a1347a238eaf1d77bd038c619bb6412a6a))

* &lt;bot&gt; update requirements-actions.txt ([`0e4a013`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0e4a0131fb34a7b8b0c4eb867d55237778395d17))

* tweak log levels in sync_gws_mailing_lists ([`aec4d30`](https://github.com/WIPACrepo/keycloak-rest-services/commit/aec4d309ec7e674451e6207e5cca800643c4a23a))


## v1.4.17 (2023-07-25)

###  

* Add &#34;group does not exist&#34; exception (#92)

* add GroupDoesNotExist exception to krs.groups

* update tests for groups.GroupDoesNotExist ([`a996550`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a996550b57fd5c448325471aaa5de41752523271))


## v1.4.16 (2023-07-25)

###  

* better handle missing &#39;email&#39; attr in sync_gws_mailing_lists ([`ea9c41a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ea9c41adf39795351b1d7efcf5c644a29378dc3d))

* make group_info_by_id recursively flatten attribute values (#91)

* make group_info_by_id recursively flatten attribute values

* &lt;bot&gt; update requirements-actions.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`3f4a83d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3f4a83d1a250f6a7fd2801dd606f22e1595f90de))


## v1.4.15 (2023-07-25)

###  

* clarify function of krs.group --new-group-path cli option (#88)

* clarify function of krs.group --new-group-path cli option

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* change modify_group parameter from new_group_path to new_group_name

* &lt;bot&gt; update requirements-actions.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`77442a0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/77442a0cddea53281a7cd0be60b6da0f9c73853e))


## v1.4.14 (2023-07-25)

###  

* &lt;bot&gt; update requirements-actions.txt ([`73036fd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/73036fd95c3c83c91693e0e2fa1a97dbcb580c5d))

* add unsubscription notification to deprovision_mailing_lists (#87)

* add unsubscription notification to deprovision_mailing_lists

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* make flake8 happy

* fix function signature

* update docstring

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`bd30ce4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bd30ce48d41cbec61a70e4be312286727343ba5f))


## v1.4.13 (2023-07-24)

###  

* handle empty &#39;email&#39; attr in sync_gws_mailing_lists ([`04eee85`](https://github.com/WIPACrepo/keycloak-rest-services/commit/04eee859fb8cac473b88c66468db7793b636c812))


## v1.4.12 (2023-07-24)

###  

* better handle missing &#39;email&#39; attr in sync_gws_mailing_lists ([`b933136`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b933136be9ccdf90eed565ebd10ac40035f17561))


## v1.4.11 (2023-07-24)

###  

* fix typo ([`f6b7fcd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f6b7fcd2b0238a845166e9d009afdd515c39f887))

* handle missing allow_members_from_experiments in deprovision_mailing_… (#89)

* handle missing allow_members_from_experiments in deprovision_mailing_lists

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`21e3078`](https://github.com/WIPACrepo/keycloak-rest-services/commit/21e307813a47a68e52088b5886d1f7aace829c17))


## v1.4.10 (2023-07-21)

###  

* support for modifying group attributes from command line (#86)

* support for modifying group attributes from command line

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* make modify action of groups consistent with users

* error checking and attribute deletion

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`2809902`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2809902d74b9e89d88684034b951a90dd1bb7eee))


## v1.4.9 (2023-07-19)

###  

* make sync_gws_mailing_lists support group member roles (#85)

* make sync_gws_mailing_lists support group roles

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* style improvement

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`cd38c3d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cd38c3de1eec524f06244661e2d89579f1d28c48))


## v1.4.8 (2023-07-17)

###  

* add sync_gws_mailing_lists action (#84)

* add sync_gws_mailing_lists action

* minor fixes ([`02a37ea`](https://github.com/WIPACrepo/keycloak-rest-services/commit/02a37eab1000a105cc5dd027711db85c79167ef4))


## v1.4.7 (2023-07-17)

###  

* pin semantic release to old version that worked ([`5aa2595`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5aa259539ae1d08fc1d5929c4c8f6e1fd813a6c8))

* talk to old servers via ssh-rsa, like i3mail (#83)

* talk to old servers via ssh-rsa, like i3mail

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`d1da17a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d1da17af6f7d18e5bbdd8b4392c1d9af7f0ac2fb))


## v1.4.6 (2023-07-13)

###  

* add deprovision_mailing_lists action (#82) ([`3a10436`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3a10436674fed7c6edcdf41fce30e40222ac545a))


## v1.4.5 (2023-07-13)

###  

* delete update_institutionless_users action ([`88dd2d8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/88dd2d8cebf08ff94f8efb784ebf8f9871fe8f87))


## v1.4.4 (2023-07-13)

###  

* &lt;bot&gt; update requirements.txt ([`62b572e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/62b572e9c338cec9f74b0367e083b61b244f0a7d))

* &lt;bot&gt; update requirements-tests.txt ([`2418a6a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2418a6a9d54ed944823807832648b74915dab432))

* &lt;bot&gt; update requirements-actions.txt ([`b210347`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b21034725c8f4eb7ea96ec3682dd0cf61aa51f65))

* rename update_user_institutions to track_user_institutions ([`f0cb56b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f0cb56be4864663dd8a210268fcbc1369425f797))


## v1.4.3 (2023-07-12)

###  

* add action to track users&#39; institutions (#81)

* add update_user_institutions action

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`7572b5b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7572b5be610576589af9ae5f30168f7ebb228da2))


## v1.4.2 (2023-07-11)

###  

* try testing list user attrs (#80)

* try testing list user attrs

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* keycloak converts int to string

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`d18c06b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d18c06bb8e6d807f7245b3b3a4389e5e09ac93d8))


## v1.4.1 (2023-07-07)

###  

* Add action to manage institutionless_since attribute (#78)

* add update_institutionless_users action

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`565474e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/565474e8c84fb64ca9e438ee9f44b0e69580338f))


## v1.4.0 (2023-05-31)

### [minor]

* [minor] use device login to allow users in master realm to login (#77)

* use device login to allow users in master realm to login

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* fix flake8

* update dockerfile build

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`49ed19f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/49ed19fc87b94a17130bc145fd4d643f693d0ad0))


## v1.3.10 (2023-05-24)

###  

*  bump py-versions CI release v2.1 (#76)

* bump py-versions CI release v2.1

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`4951345`](https://github.com/WIPACrepo/keycloak-rest-services/commit/49513458dc5a4a1e24369880136bddcaa5dee415))


## v1.3.9 (2023-05-05)

###  

* add canonical_email alias when creating new google workspace accounts (#72)

* add canonical_email alias when creating new google workspace accounts

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`9d48eb9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9d48eb9a6589115cad7cfa5ec154475d479f1adf))


## v1.3.8 (2023-05-01)

###  

* implement canonical_email user attribute

`canonical_email` is the &#34;From:&#34; address that is supposed to be used when users send email.

Historically it has been a requirement from leadership that IceCube&#39;s mail server use canonical addresses of the form firstname.lastname@icecube.wisc.edu, rather than username@icecube.wisc.edu.

`canonical_email` attribute records what this canonical address is for a user. Note that the algorithm used to generate the address from the user&#39;s name hasn&#39;t remained constant, and some users have completely custom canonical addresses, so the only way to be sure what the canonical address should be is to use this attribute. ([`088cf94`](https://github.com/WIPACrepo/keycloak-rest-services/commit/088cf9446f5fb555bc08a8a404eedc03f1954400))


## v1.3.7 (2023-04-20)

###  

* remove extra pyjwt dep, since it gets pulled in through wipac-rest-tools (#70)

* remove extra pyjwt dep, since it gets pulled in through wipac-rest-tools

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* upgrade actions versions

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; add py.typed file(s)

* fix py versions

* add logging on http error to see what changed with keycloak api

* emails need an @ sign to be valid now

* clear some actions warnings

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`fc0a6ad`](https://github.com/WIPACrepo/keycloak-rest-services/commit/fc0a6ad9004af23f1a1a5015cb77df3ec4769edf))


## v1.3.6 (2023-02-22)

###  

* &lt;bot&gt; update requirements.txt ([`f3c8ca5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f3c8ca59af5cb2b095d21b0cfb48fc00bab08b86))

* &lt;bot&gt; update requirements-tests.txt ([`4c968de`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4c968de2c6ca14c239a8ed116d80baf075bb4d24))

* &lt;bot&gt; update requirements-actions.txt ([`a2a5d90`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a2a5d90ac4d6a455e97a4b3760119c11fdf5ed91))

* make python packages used by actions scripts optional (#68)

* make python packages used by actions scripts optional

* add author details to match newer py-setup

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update requirements-actions.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* also install actions deps for tests

* fix docker build

* need to copy both reqs files into the container

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`65574bf`](https://github.com/WIPACrepo/keycloak-rest-services/commit/65574bf1bd7390e2d8143077efd56214871ecd98))


## v1.3.5 (2023-02-14)

###  

* add a tls cert to the test image (#69)

* add a tls cert to the test image

* try with full path

* more accurate timeout, and if we hit the timeout, actually raise the full error ([`bb50f7d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bb50f7dac81cc5f46e41ad421084feadda8cdb4c))


## v1.3.4 (2023-02-09)

###  

* &lt;bot&gt; update requirements.txt ([`24299c6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/24299c60a92edc1ebb47dd283e67a8ed7466bf36))

* Add CodeQL workflow for GitHub code scanning (#65)

Co-authored-by: LGTM Migrator &lt;lgtm-migrator@users.noreply.github.com&gt; ([`ff2a261`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ff2a26108a0d9895aa15c2b185e42abfa4232fa9))


## v1.3.3 (2022-11-01)

###  

* &lt;bot&gt; update requirements.txt ([`76c5102`](https://github.com/WIPACrepo/keycloak-rest-services/commit/76c5102019769b811a3359be717b87473450f702))

* remove account suspension code from sync_gws_accounts ([`7858b03`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7858b037b3a67cb6e1c48274208a449935bee392))


## v1.3.2 (2022-10-26)

###  

* Remove circleci build badge from README.md ([`6c43bc4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6c43bc4b03cb11102a68d06dcb8736e882b1cbb7))


## v1.3.1 (2022-10-25)

###  

* move tests from circleci to gh actions (#64)

* move tests from circleci to gh actions

* &lt;bot&gt; update README.md

* &lt;bot&gt; update requirements.txt

* try using the keycloak docker image we just built as a service, instead of manually running docker

* add job env

* fix yaml format

* fix yaml format again

* &lt;bot&gt; update requirements.txt

* set keycloak admin password

* need to specify command

* update rabbitmq jar file

* fix jarfile

* add ldap service image

* try running in a container, to get container networking

* try using the python image

* allow configuring the rabbitmq url

* add debugging, since tests are failing

* try adding a retry, since this seems to fail for the first test in CI

* run tests with debug logging

* update rabbitmq routing key to use glob

* try removing search term for inst list

* revert routing key changes.  add more debugging, and allow sleeping longer for listener to run.

* try improved logging

* syntax isn&#39;t working in setup.cfg

* &lt;bot&gt; update setup.cfg

* properly decorate fixture

* missing import

* fix more async fixtures

* &lt;bot&gt; update requirements.txt

* &lt;bot&gt; update requirements.txt

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`3903bcc`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3903bcc53a5da900f05a11c044e42bf5c2c05663))

* Merge pull request #62 from WIPACrepo/sync-users

New feature: sync KeyCloak user accounts to Google Workspace ([`41fbecb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/41fbecb1c4ac8ce1a14edfe692d4c9a87b2d614a))

* Merge branch &#39;master&#39; into sync-users ([`c0738ef`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c0738ef484ce484242c5faf3fa952dd19512d6d3))

* &lt;bot&gt; update setup.cfg ([`5d35abd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5d35abde2b96c36fce6a320fa7b68c4f6db85140))

* sync_gws_accounts.py: address reviewer comments ([`63b4da6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/63b4da6bd872f99f3ef5992631ecf224e3c66713))

* &lt;bot&gt; update requirements.txt ([`857db08`](https://github.com/WIPACrepo/keycloak-rest-services/commit/857db082638ad86610e2d13ccff9e3904f94aed9))

* &lt;bot&gt; update setup.cfg ([`061325f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/061325f305607141e3e87623bc30d5ed27e9db51))

* Update readme (#63)

* update testing section in README.md

* &lt;bot&gt; update requirements.txt

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`eadb59c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/eadb59c92a056cdf59da3c8ee1d05d116f6eb994))

* &lt;bot&gt; update requirements.txt ([`6ce9317`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6ce9317119007f27ac7a3367606f518e6b4f93bf))

* add test_get_gws_accounts() to test_sync_gws_accounts.py ([`9835af2`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9835af2b1e939f9a8ce1737ab5e07ca95ad7ded8))

* &lt;bot&gt; update requirements.txt ([`9f17d14`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9f17d14c45568808c72159bf25a4bebccfeb9ec9))

* add actions/sync_gws_accounts.py ([`4c7dfc7`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4c7dfc7266c47e8285f7395169168dc66c971f60))


## v1.3.0 (2022-08-16)

### [minor]

* [minor] fix QUOTAS dict to use &#39;username&#39; for ceph quota paths (#60) ([`3b3b355`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3b3b35557e9cea3b8b4bb8c61a1ae038c2bc3ce8))


## v1.2.10 (2022-08-15)

###  

* minor: add commands to create ceph quotas and directories (#59) ([`5f1f5ee`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5f1f5ee57e20ca552adad5396b49855a251c7005))


## v1.2.9 (2022-08-15)

###  

* rebuild with different options (#58) ([`431374c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/431374c45748a0193b2b80827a014ca57be505ad))


## v1.2.8 (2022-08-15)

###  

* build keycloak image in CI (#57)

* build keycloak image in CI

* add labels to image ([`f7fc016`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f7fc016321de45c337b9ea273bd23d537c5d5b1e))


## v1.2.7 (2022-08-12)

###  

* &lt;bot&gt; update requirements.txt ([`a41e5bd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a41e5bd7109b5868f60dc22e63eb4e9a2a99d462))

* build the new keycloak image for testing - allows specifying the command via env for github actions services ([`371949e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/371949ef2e8760f30d34eb1ee8d8d5a8ade063f2))


## v1.2.6 (2022-06-24)

###  

* add check for non-negative expiring users ([`8496901`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8496901e9c167155d5a7de8feec70ec5760bd655))


## v1.2.5 (2022-06-24)

###  

* also login to dockerhub, if we&#39;re pushing there ([`cb12eab`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cb12eabbc786e7d4dd64578edca3f2abf9efc3c0))


## v1.2.4 (2022-06-24)

###  

* must use PAT to trigger tag builds ([`6fa561b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6fa561bb279558f9b08ff60b65f6921f50ee7783))


## v1.2.3 (2022-06-24)

###  

* build docker images on tags ([`399f31f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/399f31f74f74080fd4e938d3d21a56b17e0809dc))


## v1.2.2 (2022-06-24)

###  

* test password expiration email action (#56)

* test password expiration email action

* &lt;bot&gt; update requirements.txt

* fix flake8 and test

* import time

* create posix account first

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`4fd3448`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4fd3448837e3a6df1b4813061c701c36a31845b7))


## v1.2.1 (2022-05-12)

###  

* match up version files ([`12ad981`](https://github.com/WIPACrepo/keycloak-rest-services/commit/12ad981e2918a2a9d968326150f7be624c08f3c9))

* modify first and last names and email (#54)

* modify first and last names and email

* bypass pip-tools error

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update requirements.txt

* add better error messages for keycloak validation

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`f0cefb1`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f0cefb1a7009e220f10d9c73f2210d597f855b92))

* &lt;bot&gt; update requirements.txt ([`c837665`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c8376656d8968667a615694ec8ad3aab8780915d))

* &lt;bot&gt; update setup.cfg ([`2f374c1`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2f374c1471742743db4a28724697b703b4f28627))

* update python setup and flake8 ([`a768eec`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a768eec413e10baa878233315768dae3d8314bca))


## v1.2.0 (2022-04-04)

### [minor]

* [minor] Flake8 fixes (#53)

* fix flake8 action

* move more things to GH actions ([`02548ed`](https://github.com/WIPACrepo/keycloak-rest-services/commit/02548ed28b4add44d5625441c56983a6a838afe4))


## v1.1.18 (2022-04-04)

###  

* &lt;bot&gt; update requirements.txt ([`dd45a4f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/dd45a4f1ac7a33bf2b3eb18df2596a079cb628ea))

* fix import for from_environment ([`ac8e594`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ac8e594691d17d15b78d31c5c66c69aecedd4dc9))

* &lt;bot&gt; update requirements.txt ([`84c6301`](https://github.com/WIPACrepo/keycloak-rest-services/commit/84c6301fd899ceb998c5b8697fe587e58c08a335))

* &lt;bot&gt; update README.md ([`3256e04`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3256e048dcdbdbee795ecec6edbc4b4e046a538b))

* &lt;bot&gt; update setup.cfg ([`90e62e4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/90e62e45076a04d9901f08670de61b3e0a4f8c59))

* bump py-setup-action version ([`b0f208a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b0f208a6472033190dedd37df197215558592183))

* first try at new wipac ci/cd action ([`3de83e6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3de83e67c65679d6bd199e6f182e743ffcc75a61))


## v1.1.17 (2022-04-04)

###  

* remove user_mgmt into its own repo (#51)

* remove user_mgmt into its own repo

* remove circleci test

* remove circleci test take 2 ([`cde39d0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cde39d040ea98a644313391f570e949db487d423))


## v1.1.16 (2022-03-04)

###  

* try for better unicode handling, and handling a space in a name (#45)

* try for better unicode handling, and handling a space in a name

* fix flake8 errors ([`7b39f52`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7b39f524594c103192eb7a5374a0fa6514b7517d))


## v1.1.15 (2022-02-21)

###  

* handle differences in attrs for list_insts_flat, by using a whitelist (#44)

* handle differences in attrs for list_insts_flat, by using a whitelist

* try fixing tests

* sort insts, to make results consistent

* fix test ([`bd4fecd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bd4fecd0f4dd77d716f68f0b3205354f0e7149c8))


## v1.1.14 (2021-12-28)

###  

* fix tests ([`105e241`](https://github.com/WIPACrepo/keycloak-rest-services/commit/105e241999a6b3da0d196621066848217a24f18a))

* fix uid/gid lookup ([`02b4b03`](https://github.com/WIPACrepo/keycloak-rest-services/commit/02b4b0368e2ac97405c4ae30e5b30b54eff9b4b1))


## v1.1.13 (2021-12-28)

###  

* import getpass ([`3b9ba5e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3b9ba5e2de6848ef488daf4d63a3860bd17a7470))


## v1.1.12 (2021-12-28)

###  

* fix flake8 errors ([`bff5648`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bff56483c6706afd03a0ecfc0ef26c301e12e115))


## v1.1.11 (2021-12-28)

###  

* create email directory. depends on being a posix user ([`0fac3d3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0fac3d3d4efc033fbaa62b1cfc05c5efd1f6fb7c))


## v1.1.10 (2021-12-21)

###  

* add an action to update the shadow expiry in LDAP ([`916e18e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/916e18edb469f9a503e1590bfe8ea793e812ff0d))


## v1.1.9 (2021-12-20)

###  

* allow tokens to other realms, for client service accounts ([`83aef1c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/83aef1cf6ee06b69b0a7514ed2ca4bdaa2877436))


## v1.1.8 (2021-12-16)

###  

* allow krs to be installed as a library so other packages can use it ([`071ffa0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/071ffa0820d33d093f9e189101115106dd3c9c77))


## v1.1.7 (2021-12-15)

###  

* add confirm popup message for all buttons except registration ([`c9489a5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c9489a55d01c51523f60b091f79e750124d54498))


## v1.1.6 (2021-12-10)

###  

* fix tests ([`2105abd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2105abd8b2d4ada987d12bedca799f7f57bcfa0a))


## v1.1.5 (2021-12-10)

###  

* send emails to inst/group admins when their approval is necessary ([`d293e4b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d293e4bbeb408a1d32663f283bbc5935ec1ec4cf))

* fix ldap component for fullname. fix tests ([`097f1da`](https://github.com/WIPACrepo/keycloak-rest-services/commit/097f1da709d7276adfbba6eac1d0fa60162114c3))


## v1.1.4 (2021-12-08)

###  

* fix canonical email address uppercase issues ([`f8e171e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f8e171e55967185c8c90e70fa5d466f673312ac5))

* add search option when listing users ([`495de4f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/495de4f21d4552b84ecfbe72264da9dd7ff83d88))


## v1.1.3 (2021-12-08)

###  

* add fullname = cn LDAP mapper, for history ([`00e7b33`](https://github.com/WIPACrepo/keycloak-rest-services/commit/00e7b334ed4bb61cb008d81c443a0bd7ed47c720))

* allow setting temp passwords from cmdline ([`e17837e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e17837e9086107de18618aa836a1e0cd31fd13bc))


## v1.1.2 (2021-12-08)

###  

* remove homeDirectory empty attr ([`966ad1c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/966ad1c601c5f7a4a99c7e442e16307a348c1b88))


## v1.1.1 (2021-12-08)

###  

* user names should be lowercase, with 16 char limit, and check if it&#39;s already used, then add a number ([`da38f32`](https://github.com/WIPACrepo/keycloak-rest-services/commit/da38f32365b87a537ee685b4ddd5c811f5424072))


## v1.1.0 (2021-12-07)

### [minor]

* [minor] cleanups for action scripts to match historical usage. ready for prod. ([`ecf230c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ecf230cd99a0ed909781a86a0898075507d71d12))


## v1.0.56 (2021-12-07)

###  

* only query exact usernames, which fixes a bug with names that are similar. also, add a dryrun option to the posix account action ([`1c2c658`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1c2c658a04240ffe9892710f92c5508e00b6c508))


## v1.0.55 (2021-12-05)

###  

* fix bug with multiple insts in the same exp fail super admin auth ([`923125f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/923125f920d95acd5740a18630bf4231b3abbcf9))


## v1.0.54 (2021-12-05)

###  

* attemt to make admin inst loading faster by only getting and caching the inst groups ([`83d6c7b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/83d6c7b018919b041413caca6af90325686566b5))


## v1.0.53 (2021-12-05)

###  

* move cache init one level higher so it survives across requests ([`249e686`](https://github.com/WIPACrepo/keycloak-rest-services/commit/249e6865bcd9805174c037467990bae7ceff6680))


## v1.0.52 (2021-12-05)

###  

* add a long cache test, and add logging ([`9193d46`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9193d4622895f553fe7546317bc313a614016ff3))

* also do prefix group checking for all other places ([`b1ad974`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b1ad9742ddc644318592cc686bba776967b9a20a))

* prevent matching groups with same prefix ([`06a3910`](https://github.com/WIPACrepo/keycloak-rest-services/commit/06a3910aea3d2d88b695270e4fae5580e09daec2))


## v1.0.51 (2021-12-05)

###  

* cache groups in the user_mgmt layer to speed up interface ([`1ebcf72`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1ebcf7295f346cce298ae10d3ea004ad69a20452))

* speed up adding and removing users from groups by removing an extra call to keycloak ([`b567f8e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b567f8eaaa2c5d11be339c2fffe72e1d12f82df7))

* remove debugging lines from icecube_ldap import ([`59bd61d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/59bd61d91a056d8073f16221eac914c87ac03c5c))


## v1.0.50 (2021-12-04)

###  

* slightly faster membership, since we don&#39;t have to call keycloak twice for small groups ([`5a72f4b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5a72f4bda6df269c198e1ec344331aa7ed6503ff))


## v1.0.49 (2021-12-04)

###  

* paginate group membership because it is super slow when LDAP is connected ([`a617ba5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a617ba59c41addf6d9ee690110be29252310c3f4))

* add every ldap user to /posix ([`18b341e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/18b341e98be7af0334c9764b4d988ed9d9b19e79))


## v1.0.48 (2021-12-03)

###  

* administering insts and groups docs ([`36ff79a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/36ff79a4cc36425f8a639701dba6bf4abc4da69f))


## v1.0.47 (2021-12-03)

###  

* add profile and pwd reset pages ([`2dd664c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2dd664cbe4c2559eefe4f6731ffff1159c66c569))


## v1.0.46 (2021-12-03)

###  

* fix password reset text ([`af84056`](https://github.com/WIPACrepo/keycloak-rest-services/commit/af8405631298826b91de74b8c8219f61b4213114))


## v1.0.45 (2021-12-03)

###  

* add page images for user login info ([`07481bb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/07481bb230217469321e1cdd807fd5d6eda7ed1b))


## v1.0.44 (2021-12-03)

###  

* add emails for approve/deny of groups. properly test for emails. ([`dcc04fc`](https://github.com/WIPACrepo/keycloak-rest-services/commit/dcc04fca8f461f55ca6632504ebff9b68b686e7a))

* user docs ([`5321da2`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5321da20e2ebf056ae43a190d93fbb450e4f5a77))


## v1.0.43 (2021-12-03)

###  

* fix tests with rabbitmq ([`b739eb8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b739eb869e4073522e725e7b2afc7be6eefaa5d2))

* some fixes for importing groups from LDAP, after live testing ([`697cbcd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/697cbcd98586eda4a1941a0c547dd21a8edb464f))

* update theme to allow external email changes ([`c3968e3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c3968e3ce65b3b1ec82f7771fc619a97480feb19))

* silence LGTM alert, since this script is run by an admin ([`9828065`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9828065fc830691674ad7f3cb900c84f660bd9be))

* add author name as a user attrib ([`a90e49c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a90e49c6283460847ba9f86edb8a2a87d970bd90))

* general script for importing authors.  will need testing after users exist in keycloak ([`54f1d7f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/54f1d7f64bfed8c969899cebce5a58b78861f346))

* fix LGTM error ([`8a371a8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8a371a890cbcdc65c8467c00491550b210849385))

* fix flake8 failures ([`3b10183`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3b101833ee98df7117acf39d58b1c74ec1eb494a))

* add name and has_mou fields ([`9475160`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9475160acaad5f2d9b9b3b9a6dd40e06eb657e76))

* add institution helpers ([`0937f73`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0937f731d710a688ba552cefae07be645d7977e0))

* change to North America ([`9e59be3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9e59be3cabe5556509645a9f5b3ab7f604faf343))

* missing import ([`e6d6347`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e6d63474f6520c4f7cf02282b26cb1f875ed9bf8))

* properly sync institutions with LDAP.  also do Gen2 institutions now ([`04bf1d1`](https://github.com/WIPACrepo/keycloak-rest-services/commit/04bf1d1518d6e877afe7e6ee012dd959f47b68a0))

* better modification of user/group attribs ([`743061d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/743061d2b205c526d2adb505fb10f0d2859736a3))


## v1.0.42 (2021-11-30)

###  

* add docs on the docs ([`bb993b3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bb993b3bee406d63be482ee821ce0e9d64c0f68c))


## v1.0.41 (2021-11-30)

###  

* set up user docs ([`daeb036`](https://github.com/WIPACrepo/keycloak-rest-services/commit/daeb03688851428ea71d41d88790e002ae88246a))


## v1.0.40 (2021-11-29)

###  

* use uid/gid for quotas. fix user vs users ([`3c6997f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3c6997fe73ca02deacd586b898de2b2ee5cb1858))


## v1.0.39 (2021-11-12)

###  

* fix flake8 and test ([`63e8421`](https://github.com/WIPACrepo/keycloak-rest-services/commit/63e8421ad7aa4ba424009da55f20ce0975a7f9fa))


## v1.0.38 (2021-11-12)

###  

* add posix group when creating posix user. closes #31 ([`dff01c2`](https://github.com/WIPACrepo/keycloak-rest-services/commit/dff01c231d20c06f2bc877e047affdd3b5284850))

* import ldap groups. closes #32 ([`03608bc`](https://github.com/WIPACrepo/keycloak-rest-services/commit/03608bcbbad4e97df28bce86f840eb5e132046e2))


## v1.0.37 (2021-11-11)

###  

* fix escaping of newline ([`4d4cdfe`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4d4cdfec2985d4959827f2c438ddefb945ce0fdd))


## v1.0.36 (2021-11-09)

###  

* optimize several calls for group membership to avoid a double keycloak lookup ([`913f2b8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/913f2b85ee6f49324bb8c31c4f52dae11fac9624))


## v1.0.35 (2021-11-09)

###  

* parallelize inst and group member retrieval ([`882fa91`](https://github.com/WIPACrepo/keycloak-rest-services/commit/882fa91d6639c9b77e28ae654bc6e2a497ad60db))


## v1.0.34 (2021-11-08)

###  

* fix super admin privs for user_mgmt. fixes #30 ([`36a33d4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/36a33d468c415918658e6e006d972d517bca5f57))

* minor fixes for email account creation ([`8babb9c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8babb9c0c48fd523d45c9f5cb612bcbe7ea6a2fe))


## v1.0.33 (2021-11-05)

###  

* fix tests ([`e0442d8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e0442d85964bc362656ee9f43f119b5a9c2ae396))

* change to uid here as well. add more logging. fix listener ([`3027962`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3027962f9672be4b993a08af66acad975c4b9df3))


## v1.0.32 (2021-11-05)

###  

* fix quota formatting for python 2.6 (nfs servers are oooold) ([`44985f3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/44985f350d1f5027e205bed19b78d1891cd3c11e))


## v1.0.31 (2021-11-05)

###  

* formatting breaks with quotes, so remove them ([`b2609e4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b2609e4bec84acbbc5f23ac498017da961582611))


## v1.0.30 (2021-11-05)

###  

* fix logger name ([`106a507`](https://github.com/WIPACrepo/keycloak-rest-services/commit/106a5071700739ea04ac68f4ef5fd06cfe04b7fc))

* define root_dir in script ([`a53c079`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a53c079f4be15a8c6b6d3e8d1420d8a12ce2b9ee))

* fix flake8 ([`e4efec0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e4efec039b17731cbc7d87a4f7ce699525984614))


## v1.0.29 (2021-11-05)

###  

* call quotas with uid instead of username, in case machine doesn&#39;t have LDAP set up ([`90594e0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/90594e053be19cfeb2a361a0b6548f6e3bf68e91))


## v1.0.28 (2021-11-05)

###  

* debug run user ([`7cb092e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7cb092e28ccc8e4fa6cc03dad2f1db2f8d2f7ef5))


## v1.0.27 (2021-11-05)

###  

* let stderr through for ssh ([`5559a67`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5559a679c0a5d76248cc17bdd37277bf62a25da3))


## v1.0.26 (2021-11-05)

###  

* fix listener, and add more logging ([`eedfde3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/eedfde37f6a16e3993a1819cddb93beaa7fe8e96))


## v1.0.25 (2021-11-05)

###  

* run ssh command as root ([`fa34b47`](https://github.com/WIPACrepo/keycloak-rest-services/commit/fa34b4793250a768ac19de4f8c0aed4719d6bfef))


## v1.0.24 (2021-11-05)

###  

* be consistent about log-level argument name ([`890b4f8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/890b4f82650056b44d00aa7fdfe66f2b8310a27b))


## v1.0.23 (2021-11-05)

###  

* correctly parse octal mode ([`8ee6850`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8ee68504c038b538eee744b76cb01a2525f8cd5e))


## v1.0.22 (2021-11-05)

###  

* action script for directory creation via ssh ([`c7db433`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c7db4332d5f43b383d7a5dbc5437880bb6b17dd2))


## v1.0.21 (2021-11-04)

###  

* get package versioning working correctly, so traces can see that ([`1779656`](https://github.com/WIPACrepo/keycloak-rest-services/commit/17796566aabd43b364e2f64b9230a8b241199420))


## v1.0.20 (2021-11-02)

###  

* update rest-tools to fix debug log messages appearing when they shouldn&#39;t be ([`048ff23`](https://github.com/WIPACrepo/keycloak-rest-services/commit/048ff23edbe443e79d5ce826a2df066a91259517))


## v1.0.19 (2021-11-02)

###  

* fix recursive feature ([`375d06b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/375d06b4f84e022a23b7bced671916a8b24cf54c))

* make flake8 happy ([`544a108`](https://github.com/WIPACrepo/keycloak-rest-services/commit/544a10884b2be07cdf23cf765527a7738b658e91))


## v1.0.18 (2021-11-02)

###  

* allow not syncing recursive (nested) groups to ldap ([`bf43bfd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bf43bfd6f7dcd2e6cf206b918419575d16f6cfb0))


## v1.0.17 (2021-11-02)

###  

* new users in /posix by default.  IceCube inst approvals also apply to IceCube-Gen2. ([`baf69e8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/baf69e85866aa217072c44c6faae920619d89e92))


## v1.0.16 (2021-11-01)

###  

* add ldap groups and syncing ([`6169c32`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6169c3286abb8fe6b1a1b030550020fd2b3f45e4))

* update to new k8s version, which might not fill in value ([`db0b0ef`](https://github.com/WIPACrepo/keycloak-rest-services/commit/db0b0efcf4b36ca8bdfa0bdb18a070613da502bf))

* add ldap group manipulation to lib, with tests ([`1fbf498`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1fbf49815963b42ca6ddb415ba357968bd5af227))

* make tests pass again by enabling rabbitmq ([`5234073`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5234073adfe7e5ec475098ebea8ca24b6e64ce6e))

* add another group test to verify which group a user gets added to when they have the same name ([`d9354f7`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d9354f73c0cb304b4cf207bf07a50defee5bbbb7))

* convert print to logging ([`0da732a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0da732aaa4f3978b367611ad9de35b7c07b3c1e5))


## v1.0.15 (2021-10-21)

###  

* use citation for author list given by Gwen ([`bb08b4d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bb08b4d932bd429c7756d21a17fc89a0339dbbcc))


## v1.0.14 (2021-10-19)

###  

* email must have Date field to be RFC-compliant ([`42a484b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/42a484b95af79149c8a19e9c8ad53d0fd864f4ad))


## v1.0.13 (2021-10-19)

###  

* add an SMTP timeout ([`08292c6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/08292c6cee41073694d15f2c12ec650db0dc7760))


## v1.0.12 (2021-10-19)

###  

* bump version of rest_tools to fix token expiration issue ([`85a524c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/85a524cf98568c536a3f134b5211bc7fdb1899a5))


## v1.0.11 (2021-10-19)

###  

* make sure new user temp password is a string ([`ca928ac`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ca928ac740a7f809fc08f0d4e612fd450a09f7d7))


## v1.0.10 (2021-10-19)

###  

* fix flake8 ([`df5ab7d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/df5ab7dfaa5c0f762b7f30f0976290bd240fb180))

* try not using iframe for js keycloak init ([`73502af`](https://github.com/WIPACrepo/keycloak-rest-services/commit/73502af41a6e3f5da8fa52754c1f5778acc0ebf6))


## v1.0.9 (2021-10-15)

###  

* Add Institutions: UC Louvain and Academia Sinica (#25) ([`3ad14b7`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3ad14b7d16d757e83c98d95cce09a6df1120f632))


## v1.0.8 (2021-09-23)

###  

* add columbia university ([`e50dbad`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e50dbadba33356e81e5705ac4e28a46113c7a903))


## v1.0.7 (2021-08-18)

###  

* Remove Packaging &amp; Breakout Institution List (#21) ([`750167d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/750167d76cd91107f672de8780a02c4bf959474b))


## v1.0.6 (2021-08-05)

###  

* allow option for specifying smtp server ([`cd86723`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cd86723b8a7df6bdd9ede8908fedb12082afffa1))


## v1.0.5 (2021-08-04)

###  

* fix tests ([`208846b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/208846b2ca05e39edd8ae6c717ce36e6cb1aff5c))

* new user email text ([`f53fcf7`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f53fcf727af1148c118455b9a551dd87d9c236d2))

* add email sending and tests ([`593e386`](https://github.com/WIPACrepo/keycloak-rest-services/commit/593e386a4e39ebc0cfaf3c47961867b0f42cf447))

* add account theme ([`ec35d3a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ec35d3ad8fbef6093bbe5e0bd224ffd1ec55230d))


## v1.0.4 (2021-07-30)

###  

* add quota support ([`25a5daa`](https://github.com/WIPACrepo/keycloak-rest-services/commit/25a5daa9fda367bfc003dd495846526b89479007))

* add an action to create a directory with a username ([`ae17c27`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ae17c27a67dd05345e279b14816d53bf4623a630))

* fix flake8 errors ([`e2e4a29`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e2e4a295ffebf6e07e563c6d466a04d9a4e2663c))

* create email account for users ([`e53d772`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e53d7725e618e502d57f355177f222fa2149c2b9))

* switch to bitnami rabbitmq image ([`ab8e9f2`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ab8e9f2ecae5d469e3482603c22073f193308a5b))

* add custom icecube theme for login page ([`dab907d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/dab907de8a65611e658567406341cc27b0230e40))

* increase sleep for slower CI runners ([`e651532`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e651532b49828321a4d0106411fe28198b8f6c11))

* add rabbitmq listener for create_home_directory ([`ce4ca15`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ce4ca15c2d1931d6d74ef99f82e67143bfe5c230))

* allow posix access to be disabled and re-enabled ([`3893fdd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3893fdd62f07e2a40c3d7a6014a38f714760d7b6))

* listen on all interfaces ([`4a0bde1`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4a0bde177ccca2381153d250830f1821f4c5421b))

* follow redirection to download rabbit jar ([`d8a3b9b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d8a3b9b2e96fddd6e1d30607ecb218d4d218497e))

* insert rabbitmq config for actions test ([`bce6802`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bce6802a6ea868aa95a5c7ba83726a88a83c87bc))

* add rabbitmq pub/sub for keycloak events, and make create_posix_account listener ([`299daaa`](https://github.com/WIPACrepo/keycloak-rest-services/commit/299daaa088b290c9cc3fd6d00ba557b01e065227))

* fix flake8 errors ([`a3cfe62`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a3cfe627d266d1b0d2b3f4ead1102acd07ff4641))

* add action to create home directories ([`a8868ac`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a8868ac5d7eeeaefe63745b1eb334ac47a059a9e))

* add .dockerignore to not copy env into container ([`cfbe119`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cfbe1195adfc10ab08dcea0f418f39caec3cbc42))

* sync between LDAP and Keycloak the right way ([`4faf9ee`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4faf9ee719ba979e15ce6b68a8cced446b365fc5))

* get circleci to run the new actions tests ([`e1074fd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e1074fd7174019e45bcb5c8b984d1d1ac7a3e9cb))

* make flake8 happy ([`f68f544`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f68f544d828dc153b8dbfb5d4a348c53f78f1f6b))

* add an action for creating a posix account in LDAP ([`1282c76`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1282c76919c8331a81c2d89d9a4240d5ce5daff9))


## v1.0.3 (2021-04-19)

###  

* Add Padova to Institution List (#17) ([`c34d968`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c34d968827cd319db608e6a381bf2068b67aa543))


## v1.0.2 (2021-03-25)

###  

* Semantic Release Bug Fix (#14) ([`0d2b823`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0d2b82307b3df8a006c84475f0a19ae4e57c014f))


## v1.0.1 (2021-03-25)

###  

* Add Semantic Release GH Action (#12) ([`fa5ba40`](https://github.com/WIPACrepo/keycloak-rest-services/commit/fa5ba401a13893249ce19c8a2977c4fe6664400b))

* Add Utah (#10) ([`19130b3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/19130b3da707c835a25e76263a4eef41754f5eb5))

* add flake8 test, and fix all the errors ([`7f010d4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7f010d4aaa77c782bd78e61c4ba47496ef54753b))

* add more tests for modifying a user in ldap. change parmaters for create_user to individual args instead of a dict ([`c24d972`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c24d9724494345841d47cd0b4fb561db5dfbff92))

* no ldap calls during keycloak user creation ([`0a020b9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0a020b9906758e750783dc251fe0e95607be4d52))

* attempt to add ldap image to circleci ([`ecda7ea`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ecda7ea20b3c1d3b932542f1cbfac1f8ed071a5f))

* basic ldap functionality tested ([`47364ff`](https://github.com/WIPACrepo/keycloak-rest-services/commit/47364ffca44ad059436a4d1b2c121229c0b340e4))

* fix get_token to only use access token, persuant to https://www.keycloak.org/docs/12.0/upgrading/#client-credentials-grant-without-refresh-token-by-default ([`b0bca85`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b0bca85eba5e281cef41c156046cfd59fcb9c803))

* ldap starts with basic icecube tree ([`8e09751`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8e0975187d780edfaa233f2a536b0ad4bbd26a15))

* setup.py (#4)

* copy https://github.com/WIPACrepo/rest-tools/blob/master/setup.py

* setup.py

* add user_mgmt

* add keycloak_setup instead of resources as a package ([`62ff917`](https://github.com/WIPACrepo/keycloak-rest-services/commit/62ff9179f7ac8992eb18b3982043d2ede03d694c))

* properly handle connecting to the admin db for auth ([`f44eae8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f44eae8027cae705611b05b1e9a0e40969829406))

* abbreviations, is_US, &amp; region (#2)

* abbreviations, is_US, &amp; region

* Revert &#34;abbreviations, is_US, &amp; region&#34;

This reverts commit 64ecb734cc2ea389a3a9e93cea3febe1345b36a0.

* remove excessive black auto-formatting ([`6801fac`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6801fac25fa2873732890c79fb4a70541e233755))

* sort experiments and institutions. fix when removing someone from an institution, to remove them from subgroups ([`d8841f6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d8841f65a57b22b17606ea14a21247f03669e547))

* only get subgroups instead of full institution info, reducing to a single Keycloak call for greater speed ([`e236ef2`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e236ef26b77ba396554fdc77278ecf6279dc616a))

* add all IceCube insts, and make retrieving them faster

* add attributes to groups

* attributes must be list instead of string

* properly get value of attr

* add route to get all experiment/institution info at once

* fix bad copy/paste

* request all institution info in parallel

* this should be a set, not a dict

* import asyncio

* use new all-experiments route ([`7a1d8e8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7a1d8e825fd76f568e96df0b88e3e4bcf649cbc6))

* add option for realm ([`38a8eb0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/38a8eb076bdf76211ba333e9f6f4b4f989ae471d))

* point at the correct keycloak url ([`dc83aea`](https://github.com/WIPACrepo/keycloak-rest-services/commit/dc83aeac30a2373ecefb4a18822de78e8dd0a894))

* deploy container ([`9d58c2b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/9d58c2b2dcd5908028616cbca6b9234c971eb777))

* flesh out user_mgmt api tests ([`6ed7f70`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6ed7f702030abecfb5a1adc31e5cba4bc4723b8f))

* fix test failure ([`80b1a3e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/80b1a3e5575e0cc3de12a8498453d21f4dd803a1))

* add groups admin page. get group joining working ([`04bc891`](https://github.com/WIPACrepo/keycloak-rest-services/commit/04bc891f2b04c293c63a0fa3e01a38a6905e9b89))

* allow user to leave sub-groups, but not join ([`c6fe681`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c6fe6815acf8c41ffd073017e71f9b8439c2d63a))

* admins can manipulate inst authorlist and other subgroups ([`e4c3fff`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e4c3fff1615fc47c9f53c021329276f4be255dc0))

* working admin view of an institution ([`ffdb0ed`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ffdb0eddd31effa59138f0795164478f0c486b36))

* user can join, move from, and delete institutions ([`7bb4467`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7bb4467b4ab41c7c86e9b070cd14543d5189649a))

* update setup script to previous changes ([`53c4a2e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/53c4a2e4e1d5b7e40f3a684f550e02942b5e03e9))

* fix adding user to a parent group when already in a child group. workaround for https://issues.redhat.com/browse/KEYCLOAK-11298 ([`4a8c2e9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4a8c2e9cf206344c04a77d321ceba16d2f1a62da))

* start work on user profile page ([`89adf4a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/89adf4ab5b4deabeeda3f406ed4156fcbc425128))

* successfully approve/deny a new registration ([`0fa8023`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0fa802378a2476e54d903146a7f7c50339c28082))

* fix circleci config ([`82d6b1c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/82d6b1c2abdfca4d17fc5ae1f7a92a128c90768b))

* go all-in on a rest client for krs, as we need to refresh the token while the user_mgmt server runs ([`2d2be63`](https://github.com/WIPACrepo/keycloak-rest-services/commit/2d2be63a544121fbfb6276883415af9907e51e0e))

* fix readme ([`d23e31d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d23e31d131f46c9cf3ae396edc9a7656d2555d4c))

* update readme ([`7d24686`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7d24686e2aa3fe377eacc2526e47b2fc9f8dc45b))

* full user_mgmt rest tests ([`b1358b4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b1358b46c9062dd4240ed62fdd2c5f92452cb69e))

* tests for insts section of user_mgmt ([`f4dc881`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f4dc881f8f9852312f08cfba10422e1b74b0af4a))

* convert krs to async ([`8ce2db5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8ce2db5ff106a44044293ed04381318230d82095))

* fix up tests. run krs and user_mgmt tests in parallel ([`67b4d0d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/67b4d0df943a5ed7893e62d1475b9ad5c5bddd23))

* icecube setup script ([`a2917d9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a2917d90b94d513ba733493cb11cd2d150a2f4c6))

* first instance of rest api ([`c5595e3`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c5595e35657ae3cede3adf47a895f557bd1bb624))

* set user attributes ([`c9010ed`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c9010ed50782a6a837c62aa9b3ccdbfbf89f27eb))

* get group membership ([`bd2fa43`](https://github.com/WIPACrepo/keycloak-rest-services/commit/bd2fa430d39b7cef06c4cb2941264934a50d30af))

* basic icecube realm setup ([`c0406bf`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c0406bfccc908acbb79261a2c418bde5c925c5f6))

* add toc to user stories ([`77de6ef`](https://github.com/WIPACrepo/keycloak-rest-services/commit/77de6ef26988b13434f56e7e7342d91067489e67))

* better REST info in user stories ([`118e1b0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/118e1b02c75dab3763b07739fb560020cbf98b8a))

* user stories ([`532f548`](https://github.com/WIPACrepo/keycloak-rest-services/commit/532f548066d8bf48dc1a63b2691a10dc90bafea6))

* another fix for apps test ([`b12054e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b12054ed3a774d4dfb2aea67663306417819dce2))

* fix apps for group changes ([`977df48`](https://github.com/WIPACrepo/keycloak-rest-services/commit/977df48bb8ec036fcb375cd6177addafac0953b6))

* fix a bug when creating a group without a parent ([`8d57087`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8d570876a4c6f10e5241215f5063b9364c358477))

* fix up tests for last commit ([`ec49289`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ec492891f73e30e85f18cfa24480ad7e3ecf76a8))

* use full path for groups as unique idenfitier, so we can have subgroups with the same name in different parts of the tree ([`5021584`](https://github.com/WIPACrepo/keycloak-rest-services/commit/50215847821212a4185107cb85aa51c5d3c62389))

* openid login with a local keycloak instance.  needs more refinement in address hard-coding, but good for a proof-of-concept ([`47ec9d0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/47ec9d05f8192f56ef566198d248e8b3906bd540))

* initial user registration to mongodb ([`7366404`](https://github.com/WIPACrepo/keycloak-rest-services/commit/73664049a6baa8ce48ab44f67c58ecf7f2b0912c))

* get basic Vue template working ([`1ac805a`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1ac805adefb4a644cbfe207571003b3e181338b1))

* start fleshing out user management website, with a REST API ([`3af0376`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3af0376a9aa36f5ca2f4cf0ce54b2b36511f45d4))

* remove unused scripts ([`7ca9495`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7ca9495d70cd68eb9c3ae6334060f39d138e0699))

* get a user token for an application. fixed several bugs in that process, and made more tests. ([`a612202`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a6122026cb57c69bd24aa4aa815ed359f899b4bf))

* add all the basics for supporting oauth2 applications ([`d469379`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d4693799e4f0d468297b131ee255215e591ab830))

* edit Keycloak spelling. add new group info function. ([`0efbd26`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0efbd26a33c4ad59629f13cc42e9444e03d4bb5f))

* table of contents for readme ([`a95843e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a95843e3df5cd0bea83af75bfa0e2cea0b75ce49))

* figure out coverage, and write a better readme ([`5bd1461`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5bd146165ee62398a4fae48a9d17cba5ceb5ad5c))

* add functions to get user info, and add and remove users from groups ([`7bd84c0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7bd84c0e37299f144ab04c2cce177339456e9407))

* add user and group support ([`f139bfc`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f139bfc2ce18d339463ebc4173ebf7030412ead1))

* clean up service role ([`d257abc`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d257abc0ee9ad04955ff1f718bfa7a5c938aabd1))

* need token for private project badge ([`fdb2c5e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/fdb2c5e6faa5e01e34936fe427a725f313166abc))

* circleci badge in readme ([`79e4470`](https://github.com/WIPACrepo/keycloak-rest-services/commit/79e4470197eb8cafb93a14af6ddf6d330260d9ae))

* full testing for bootstrap script ([`c9e9a97`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c9e9a97e370fce13c5db485c06faefe72e350ecd))

* enable initial testing for the bootstrap script ([`8803d7f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/8803d7fabc49510aa7e532429363d7eddc7c804a))

* how to bootstrap the rest-access client into a vanilla KeyCloak ([`d2af360`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d2af360020a29d3b691abd0a2fbe2d4cd60ddb77))

* get an admin token. handle env variables as secrets ([`311a9bb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/311a9bb7e54cc4192dba84f4e5e1e5ca16e54434))

* get a basic test working for both docker (local) and k8s (remote) ([`86806d9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/86806d988fe6fcb970ab6956a9926efec7ed613d))

* Initial commit ([`55acba8`](https://github.com/WIPACrepo/keycloak-rest-services/commit/55acba896a32abaaa03df5883034f40990097fc8))
