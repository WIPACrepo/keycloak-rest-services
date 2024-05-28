# Changelog

<!--next-version-placeholder-->

## v1.4.94 (2024-05-28)

### Other

* <bot> update dependencies*.log files(s) ([`dc5c05f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/dc5c05f59da5183f645aaba9d26d257a041628c7))
* Minor fixes ([`e9ebda4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e9ebda49cbb899aee70c072ecdccc8111a1170d2))

## v1.4.93 (2024-05-24)

### Other

* <bot> update dependencies*.log files(s) ([`70e1fdd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/70e1fddde01a837fb273216e22af64051bb99a9f))
* Sync_synchronized_groups.py ([#152](https://github.com/WIPACrepo/keycloak-rest-services/issues/152)) ([`181d38b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/181d38beff430b08b1a79933c5e9bda09500e2d4))

## v1.4.92 (2024-05-22)

### Other

* Sync_gws_mailing_lists.py: change group skipping mechanism ([#155](https://github.com/WIPACrepo/keycloak-rest-services/issues/155)) ([`eef1a73`](https://github.com/WIPACrepo/keycloak-rest-services/commit/eef1a73be0fda05298ae89b4f9bde707aa2b68f4))

## v1.4.91 (2024-05-22)

### Other

* Actions/sync_gws_mailing_lists.py: support for automation_blocklist ([#154](https://github.com/WIPACrepo/keycloak-rest-services/issues/154)) ([`79833da`](https://github.com/WIPACrepo/keycloak-rest-services/commit/79833dafb9d72d5af80fd68955694c282c0fac51))

## v1.4.90 (2024-05-22)

### Other

* Recursive mail list sync tweaks ([#153](https://github.com/WIPACrepo/keycloak-rest-services/issues/153)) ([`cf625c5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cf625c56b1a83cdfb12f4491a84ab22c9de5750d))

## v1.4.89 (2024-05-10)

### Other

* <bot> update dependencies*.log files(s) ([`7fb8acb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7fb8acb3090104babca214bbc6dfab4d9a52e995))
* Password expired email: update URL for new keycloak version ([`5c7abc0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5c7abc044da014208398f0e07710dc714d655826))

## v1.4.88 (2024-05-06)

### Other

* Add krs.groups.get_group_hierarchy ([#151](https://github.com/WIPACrepo/keycloak-rest-services/issues/151)) ([`ec96a7c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ec96a7cbd9410119417c301c063b7a31ed6f51e4))

## v1.4.87 (2024-05-06)

### Other

* Have krs.groups.list_groups include attributes ([#150](https://github.com/WIPACrepo/keycloak-rest-services/issues/150)) ([`26c87f0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/26c87f04e7436de3ff2e5c5e1519f35872e7a2e3))

## v1.4.86 (2024-05-02)

### Other

* <bot> update dependencies*.log files(s) ([`f343a1e`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f343a1ef649aab74fb2a8f88abde268b2c349e79))
* Dockerfile back to python 3.10 from 3.11 (it wasn't the problem) ([`1c9346d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/1c9346dbae3b5850ff974ad02e5aace9be94b05a))

## v1.4.85 (2024-05-02)

### Other

* Fix issue with pagination in list_users with keycloak 23 ([#149](https://github.com/WIPACrepo/keycloak-rest-services/issues/149)) ([`aa0de1f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/aa0de1f01054ce635418ed59b4bc3f04a850c16c))

## v1.4.84 (2024-05-01)

### Other

* <bot> update dependencies*.log files(s) ([`3793ebf`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3793ebfaa24515cf80638bb1506bd5b0ff44476b))
* Update python version to 3.11 ([`638b97c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/638b97c7860785560c25798c2b22e1ac375dd792))

## v1.4.83 (2024-05-01)

### Other

* Remove actions/sync_authors_mail_group.py ([`694937c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/694937cc7c5bd456cca9b44a773e760c88fa9801))
* Add sync_group_membership.py action ([#148](https://github.com/WIPACrepo/keycloak-rest-services/issues/148)) ([`4e9aa20`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4e9aa20e2e23daead130f0763f2ad146e15d0168))

## v1.4.82 (2024-04-29)

### Other

* Fix non-determinism in tests ([`d231f35`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d231f35bfce00f3389588ec0df0574cbc7cdec3f))

## v1.4.81 (2024-04-29)

### Other

* Fix tests/actions/sync_gws_mailing_lists.py ([#146](https://github.com/WIPACrepo/keycloak-rest-services/issues/146)) ([`7c01189`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7c01189cdfc9cf258d9992b4c9f2ac6a51a182aa))
* Make sync_gws_mailing_lists.py act recursively ([#145](https://github.com/WIPACrepo/keycloak-rest-services/issues/145)) ([`d62439d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/d62439d56af395f77d31d5308b1983e8c249c564))

## v1.4.80 (2024-04-25)

### Other

* Make prune_mail_groups_by_experiment.py act recursively ([#144](https://github.com/WIPACrepo/keycloak-rest-services/issues/144)) ([`639b9fe`](https://github.com/WIPACrepo/keycloak-rest-services/commit/639b9fed0dd20013b6175c4587b947a3dbfaa0f7))

## v1.4.79 (2024-04-24)

### Other

* <bot> update dependencies*.log files(s) ([`44230dd`](https://github.com/WIPACrepo/keycloak-rest-services/commit/44230ddef1c06add1436cdd365790c93b0b3a4e5))
* Add script to look up group member emails ([`5299837`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5299837712ff209d1ae3a9d203debe28f138bc7f))

## v1.4.78 (2024-04-23)

### Other

* <bot> update dependencies*.log files(s) ([`a9c6c6d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a9c6c6dab4271d2ba1821853d4472c529b310069))
* Sync_authors_mail_group.py: doc fixes ([`cf13936`](https://github.com/WIPACrepo/keycloak-rest-services/commit/cf139364e6b8a9b4fc802b8a4e7d82f53d872c5e))

## v1.4.77 (2024-04-22)

### Other

* Actions/sync_authors_mail_group.py: parametrize experiment name ([#143](https://github.com/WIPACrepo/keycloak-rest-services/issues/143)) ([`399ffb9`](https://github.com/WIPACrepo/keycloak-rest-services/commit/399ffb9ce1200b978b559a183ae37388b0c61745))

## v1.4.76 (2024-04-17)

### Other

* Update README.md ([`ae6b2a1`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ae6b2a1387e5e0770f16a0e1a8b7d82f69ef0f65))

## v1.4.75 (2024-04-17)

### Other

* Remove uid/gid from email relay creation ([#142](https://github.com/WIPACrepo/keycloak-rest-services/issues/142)) ([`4fef8a0`](https://github.com/WIPACrepo/keycloak-rest-services/commit/4fef8a04c5e30773bf954ce98884d698da5cfb8c))

## v1.4.74 (2024-04-16)

### Other

* Use keycloak 24.0.3 container ([`3312a8b`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3312a8bb8221c0e256dbc246b5ef480f5952c844))

## v1.4.73 (2024-04-11)

### Other

* Revert missing attributes experiment ([#141](https://github.com/WIPACrepo/keycloak-rest-services/issues/141)) ([`c6badc1`](https://github.com/WIPACrepo/keycloak-rest-services/commit/c6badc15ec3f81b082ad929d78427487f0e7476b))

## v1.4.72 (2024-04-11)

### Other

* Bootstrap.py: missing id token attributes experiment ([#140](https://github.com/WIPACrepo/keycloak-rest-services/issues/140)) ([`3fbbf2c`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3fbbf2c42112fede49c160d224eba3d835a5d55b))

## v1.4.71 (2024-04-09)

### Other

* Sync_gws_mailing_lists.py: handle dup owners ([#138](https://github.com/WIPACrepo/keycloak-rest-services/issues/138)) ([`efcaaa5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/efcaaa54f8a028ac7e230485e15c1ddf7e004223))

## v1.4.70 (2024-04-08)

### Other

* Use keycloak 24.0.2 for testing ([#137](https://github.com/WIPACrepo/keycloak-rest-services/issues/137)) ([`430350d`](https://github.com/WIPACrepo/keycloak-rest-services/commit/430350d14058c86150b7dfdec730425b4ce5a189))

## v1.4.69 (2024-04-04)

### Other

* Add krs.util.keycloak_version() function ([#136](https://github.com/WIPACrepo/keycloak-rest-services/issues/136)) ([`a464155`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a4641552b5ef5b174e4695cf415690b2d2b02d86))

## v1.4.68 (2024-04-03)

### Other

* Pre-keycloak-v23 compatibility ([#135](https://github.com/WIPACrepo/keycloak-rest-services/issues/135)) ([`b6221f6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/b6221f60a5998ee6fe7a70166e25b6da51c25d53))

## v1.4.67 (2024-04-01)

### Other

* Use wipac-dev-py-setup-action@v3.1 ([`327db94`](https://github.com/WIPACrepo/keycloak-rest-services/commit/327db94064e12331ffa07a70e80462b5d42f5c32))
* Sync_gws_mailing_lists.py: better notifications ([`146e337`](https://github.com/WIPACrepo/keycloak-rest-services/commit/146e33780cc4c50515dc7fddbc06c441983db66d))
* Improve removal notification email text ([#133](https://github.com/WIPACrepo/keycloak-rest-services/issues/133)) ([`77c9d39`](https://github.com/WIPACrepo/keycloak-rest-services/commit/77c9d39cb613864a8eb0c4ae96e6b215d367867d))

## v1.4.66 (2024-03-19)

### Other

* Compatibility with newest keycloak ([#132](https://github.com/WIPACrepo/keycloak-rest-services/issues/132)) ([`0dab13f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0dab13fc3cafbd16ad5f32b15005440d5f85d14f))

## v1.4.65 (2024-02-14)

### Other

* Sync_authors_mail_group.py: use authorlist* groups, not just authorlist ([#130](https://github.com/WIPACrepo/keycloak-rest-services/issues/130)) ([`7a876a6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7a876a6202cec81bab6f7ec4ca47287037b85eee))

## v1.4.64 (2024-02-13)

### Other

* Sync_gws_mailing_lists.py: fix order of operations ([#129](https://github.com/WIPACrepo/keycloak-rest-services/issues/129)) ([`ff26c27`](https://github.com/WIPACrepo/keycloak-rest-services/commit/ff26c2723650f22dbff209fd0098beb828b8a19c))

## v1.4.63 (2024-02-12)

### Other

* Sync_gws_mailing_lists.py: allow username@iwe to be preferred addresses ([#128](https://github.com/WIPACrepo/keycloak-rest-services/issues/128)) ([`0d8a4d6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0d8a4d6e51c5b2197c92a2cefd5d24db629a24ed))

## v1.4.62 (2024-02-12)

### Other

* Make exceptions make more sense in retry_execute() from actions/util.py ([#127](https://github.com/WIPACrepo/keycloak-rest-services/issues/127)) ([`f818e44`](https://github.com/WIPACrepo/keycloak-rest-services/commit/f818e4423a4b493ae0378cf0ba92d625ec5a9fdd))

## v1.4.61 (2024-02-12)

### Other

* Sync_gws_accounts.py: give time to finishing creating dependencies ([#126](https://github.com/WIPACrepo/keycloak-rest-services/issues/126)) ([`662b670`](https://github.com/WIPACrepo/keycloak-rest-services/commit/662b670cef794dac7f2493f5d4102733d8198057))

## v1.4.60 (2024-02-01)

### Other

* Implement /mail/authors ([#123](https://github.com/WIPACrepo/keycloak-rest-services/issues/123)) ([`5631eee`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5631eee512057e53f4c5dd9ebb65ad763a0c5830))

## v1.4.59 (2024-02-01)

### Other

* Rename prune_mailing_lists_by_experiment ([#125](https://github.com/WIPACrepo/keycloak-rest-services/issues/125)) ([`7925910`](https://github.com/WIPACrepo/keycloak-rest-services/commit/7925910f2fc73680b11aaba3f023d162bb41441c))

## v1.4.58 (2024-01-29)

### Other

* Actions/util.py: handle http 404 in retry_execute() ([#124](https://github.com/WIPACrepo/keycloak-rest-services/issues/124)) ([`85e6aa7`](https://github.com/WIPACrepo/keycloak-rest-services/commit/85e6aa7433d27b765c609bf441d1dac76e00d199))

## v1.4.57 (2024-01-25)

### Other

* Rename deprovision_mailing_lists.py to prune_mailing_lists_by_experim… ([#122](https://github.com/WIPACrepo/keycloak-rest-services/issues/122)) ([`28cc4a6`](https://github.com/WIPACrepo/keycloak-rest-services/commit/28cc4a6d6b8ef84bae608776cfbedab4a619d9ed))

## v1.4.56 (2024-01-23)

### Other

* Replace --sa-delegator with --sa-subject, which is more accurate ([`e809a3f`](https://github.com/WIPACrepo/keycloak-rest-services/commit/e809a3f9a84b13687fbf375dd0febad6067a96b7))

## v1.4.55 (2024-01-23)

### Other

* <bot> update dependencies*.log files(s) ([`3d8d7d4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/3d8d7d4ce58d178a6f71f0c66885de0fcb69b5f0))
* Docs update ([`58565bb`](https://github.com/WIPACrepo/keycloak-rest-services/commit/58565bb0a4d438ddf7a4d887a167bcd86af533e2))

## v1.4.54 (2024-01-22)

### Other

* Sync_gws_accounts.py: handle partial account setup situations ([#121](https://github.com/WIPACrepo/keycloak-rest-services/issues/121)) ([`a1fba78`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a1fba782c0988ef1a3529a857089eaebf8fe7e8f))

## v1.4.53 (2024-01-22)

### Other

* Utils.py retry_execute: except HTTP 500 and 503 ([`97d7cc4`](https://github.com/WIPACrepo/keycloak-rest-services/commit/97d7cc440b560180f8f7c69d248f08fb58a9c310))

## v1.4.52 (2024-01-22)

### Other

* Actions/sync_gws_accounts.py: handle more exceptions ([#120](https://github.com/WIPACrepo/keycloak-rest-services/issues/120)) ([`7825317`](https://github.com/WIPACrepo/keycloak-rest-services/commit/78253174c4bade1609235dbccdffd1599fa7867a))

## v1.4.51 (2024-01-04)

### Other

* Krs/email.py: handle addresses without domain ([#119](https://github.com/WIPACrepo/keycloak-rest-services/issues/119)) ([`5b6beba`](https://github.com/WIPACrepo/keycloak-rest-services/commit/5b6beba4f84b888815af227f06a7985ab9d59c6a))

## v1.4.50 (2024-01-04)

### Other

* Chore: fix keycloak image version for tests ([#118](https://github.com/WIPACrepo/keycloak-rest-services/issues/118)) ([`022b4e5`](https://github.com/WIPACrepo/keycloak-rest-services/commit/022b4e5d46fb5e8e4e75f5cc7d36b1ff7342fe51))

## v1.4.49 (2023-11-08)

### Other

* Sync_gws_accounts.py: fix logical error ([`6f9a990`](https://github.com/WIPACrepo/keycloak-rest-services/commit/6f9a990f8537726e0f277660fa8adb75c833a4f3))

## v1.4.48 (2023-11-08)

### Other

* Sync_gws_accounts.py: require force_creation_in_gws to be "true" or absent ([`a060c21`](https://github.com/WIPACrepo/keycloak-rest-services/commit/a060c216bd053bcc968aa5c688f9cef14f14d145))

## v1.4.47 (2023-11-08)

### Other

* Actions/create_email_account.py: remove pointless relay of alias ([`0f195e2`](https://github.com/WIPACrepo/keycloak-rest-services/commit/0f195e24a38e2c11018d22e500dbc27277265dfa))
* Add test_track_user_institutions.py test ([`9065007`](https://github.com/WIPACrepo/keycloak-rest-services/commit/90650078a9f58a2ba932a49cc1674c2d55dbaed1))

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

