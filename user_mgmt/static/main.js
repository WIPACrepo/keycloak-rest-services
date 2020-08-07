// debug flag
var krs_debug = false;

// global Keycloak object
var keycloak;


/** helper functions **/

var get_username = async function() {
  if (!keycloak.authenticated)
    return ''
  try {
    await keycloak.updateToken(5)
    console.log(keycloak.tokenParsed)
    return keycloak.tokenParsed['username']
  } catch (error) {
    console.log("error getting username from token")
    return ''
  }
};

var get_my_experiments = async function() {
  if (!keycloak.authenticated)
    return []
  try {
    await keycloak.updateToken(5)
    let experiments = []
    console.log(keycloak.tokenParsed)
    for (const group of keycloak.tokenParsed.groups) {
      if (group.startsWith('/institutions')) {
        const parts = group.split('/')
        if (parts.length != 4)
          continue
        const exp = parts[2]
        if (!experiments.includes(exp))
          experiments.push(exp)
      }
    }
    console.log("get_my_experiments() - "+JSON.stringify(experiments))
    return experiments
  } catch (error) {
    console.log("error getting experiments from token")
    return []
  }
};

var get_my_institutions = async function(experiment) {
  if (!keycloak.authenticated)
    return []
  try {
    await keycloak.updateToken(5)
    let institutions = {}
    for (const group of keycloak.tokenParsed.groups) {
      if (group.startsWith('/institutions')) {
        const parts = group.split('/')
        if (parts.length >= 4 && parts[2] == experiment) {
          const inst = parts[3]
          if (parts.length == 4 || (parts.length == 5 && !parts[4].startsWith('_'))) {
            if (!(inst in institutions))
              institutions[inst] = {subgroups: []}
            if (parts.length == 5)
              institutions[inst].subgroups.push(parts[4])
          }
        }
      }
    }
    console.log("get_my_institutions() - "+JSON.stringify(institutions))
    return institutions
  } catch (error) {
    console.log("error getting institutions from token")
    console.log(error)
    return []
  }
};

var get_my_groups = async function() {
  if (!keycloak.authenticated)
    return []
  try {
    await keycloak.updateToken(5)
    let groups = []
    console.log(keycloak.tokenParsed)
    for (const group of keycloak.tokenParsed.groups) {
      if (!group.startsWith('/institutions')) {
        const parts = group.split('/')
        if (parts[parts.length-1].startsWith('_'))
          continue
        groups.push(group)
      }
    }
    console.log("get_my_groups() - "+JSON.stringify(groups))
    return groups
  } catch (error) {
    console.log("error getting groups from token")
    console.log(error)
    return []
  }
};

var get_my_inst_admins = async function() {
  if (!keycloak.authenticated)
    return []
  try {
    await keycloak.updateToken(5)
    let institutions = []
    for (const group of keycloak.tokenParsed.groups) {
      if (group.startsWith('/institutions')) {
        const parts = group.split('/')
        if (parts.length == 5 && parts[4] == '_admin') {
          let inst = parts.slice(0,4).join('/')
          if (!institutions.includes(inst))
            institutions.push(inst)
        }
      }
    }
    return institutions
  } catch (error) {
    console.log("error getting admin institutions from token")
    return []
  }
};

var get_my_group_admins = async function() {
  if (!keycloak.authenticated)
    return []
  try {
    await keycloak.updateToken(5)
    let groups = [];
    for (const group of keycloak.tokenParsed.groups) {
      if (!group.startsWith('/institutions')) {
        const parts = group.split('/')
        if (parts.length > 2 && parts[parts.length-1] == '_admin') {
          let grp = parts.slice(0,parts.length-1).join('/')
          if (!groups.includes(grp))
            groups.push(grp)
        }
      }
    }
    console.log("get_my_group_admins() - "+JSON.stringify(groups))
    return groups
  } catch (error) {
    console.log("error getting admin groups from token")
    return []
  }
};

var get_all_inst_subgroups = async function() {
  try {
    const resp = await axios.get('/api/experiments');
    let experiments = {}
    for (const exp of resp.data) {
      const resp2 = await axios.get('/api/experiments/'+exp+'/institutions');
      let institutions = {}
      for (const inst of resp2.data) {
        const resp3 = await axios.get('/api/experiments/'+exp+'/institutions/'+inst)
        institutions[inst] = resp3.data
      }
      experiments[exp] = institutions
    }
    return experiments
  } catch (error) {
    console.log("error getting inst_subgroups")
    console.log(error)
    return {}
  }
};


/** Routes **/

Home = {
  data: function(){
    return {
      join_inst: false,
      join_group: false,
      experiment: '',
      institution: '',
      remove_institution: '',
      group: '',
      error: '',
      form_error: '',
      valid: true,
      submitted: false,
      refresh: 0
    }
  },
  asyncComputed: {
    my_experiments: {
      get: async function(){
        if (this.refresh > 0) {
          // refresh token
          await keycloak.updateToken(-1)
        }
        let exps = await get_my_experiments()
        let ret = {}
        for (const exp of exps) {
          ret[exp] = await get_my_institutions(exp)
        }
        return ret
      },
      watch: ['refresh']
    },
    my_groups: {
      get: async function(){
        if (this.refresh > 0) {
          // refresh token
          await keycloak.updateToken(-1)
        }
        let groups = await get_my_groups()
        let ret = {}
        if (this.groups !== null) {
          for (const name in this.groups) {
            if (groups.includes(name))
              ret[name] = this.groups[name]
          }
        }
        return ret
      },
      watch: ['groups','refresh']
    },
    validExperiment: function() {
      try {
        return this.experiment != '' && this.experiments !== null && this.experiment in this.experiments
      } catch(error) {
        return false
      }
    },
    validInstitution: function() {
      try {
        return this.institution != '' && this.institutions !== null && this.institutions.includes(this.institution)
      } catch(error) {
        return false
      }
    },
    experiments: get_all_inst_subgroups,
    institutions: async function() {
      if (this.validExperiment) {
        try {
          let insts = []
          if (this.experiment in this.experiments) {
            if (!(this.experiment in this.my_experiments)) {
              insts = Object.keys(this.experiments[this.experiment])
            } else {
              for (const inst in this.experiments[this.experiment]) {
                if (!(inst in this.my_experiments[this.experiment]))
                  insts.push(inst)
              }
            }
          }
          return insts
        } catch (error) {
          console.log('error')
          console.log(error)
        }
      }
      return {}
    },
    groups: async function() {
      if (!keycloak.authenticated)
        return {}
      try {
        await keycloak.updateToken(5);
        const resp = await axios.get('/api/groups', {
          headers: {'Authorization': 'bearer '+keycloak.token}
        })
        return resp.data
      } catch(error) {
        console.log(error)
        return {}
      }
    },
    validGroup: function() {
      try {
        return this.group != '' && this.groups !== null && this.group in this.groups
      } catch(error) {
        return false
      }
    }
  },
  methods: {
    submit: async function(e) {
      // validate
      this.valid = (this.validExperiment && this.validInstitution)

      // now submit
      if (this.valid) {
        this.errMessage = 'Submission processing';
        try {
          await keycloak.updateToken(5);
          let data = {
            experiment: this.experiment,
            institution: this.institution,
          }
          if (this.remove_institution != '')
            data.remove_institution = this.remove_institution
          const resp = await axios.post('/api/inst_approvals', data, {
            headers: {'Authorization': 'bearer '+keycloak.token}
          });
          console.log('Response:')
          console.log(resp)
          this.form_error = 'Submission successful'
          this.submitted = true
        } catch (error) {
          console.log('error')
          console.log(error)
          let error_message = 'undefined error';
          if (error.response) {
            if ('code' in error.response.data) {
              error_message = 'Code: '+error.response.data['code']+'<br>Message: '+error.response.data['error'];
            } else {
              error_message = JSON.stringify(error.response.data)
            }
          } else if (error.request) {
            error_message = 'server did not respond';
          }
          this.form_error = '<span class="red">Error in submission<br>'+error_message+'</span>'
        }
      } else {
        this.form_error = '<span class="red">Please fix invalid entries</span>'
      }
    },
    submit_group: async function(e) {
      if (this.validGroup) {
        this.errMessage = 'Submission processing';
        try {
          await keycloak.updateToken(5);
          let data = {
            group: this.group
          }
          const resp = await axios.post('/api/group_approvals', data, {
            headers: {'Authorization': 'bearer '+keycloak.token}
          });
          console.log('Response:')
          console.log(resp)
          this.form_error = 'Submission successful'
          this.submitted = true
        } catch (error) {
          console.log('error')
          console.log(error)
          let error_message = 'undefined error';
          if (error.response) {
            if ('code' in error.response.data) {
              error_message = 'Code: '+error.response.data['code']+'<br>Message: '+error.response.data['error'];
            } else {
              error_message = JSON.stringify(error.response.data)
            }
          } else if (error.request) {
            error_message = 'server did not respond';
          }
          this.form_error = '<span class="red">Error in submission<br>'+error_message+'</span>'
        }
      } else {
        this.form_error = '<span class="red">Please fix invalid entries</span>'
      }
    },
    leave_inst_action: async function(exp, inst) {
      try {
        await keycloak.updateToken(5);
        const username = await get_username();
        const resp = await axios.delete('/api/experiments/'+exp+'/institutions/'+inst+'/users/'+username, {
          headers: {'Authorization': 'bearer '+keycloak.token}
        });
        console.log('Response:')
        console.log(resp)
        this.refresh = this.refresh+1
      } catch (error) {
        console.log('error')
        console.log(error)
        let error_message = 'undefined error';
        if (error.response && 'data' in error.response) {
          if ('code' in error.response.data) {
            error_message = 'Code: '+error.response.data['code']+'<br>Message: '+error.response.data['error'];
          } else {
            error_message = JSON.stringify(error.response.data)
          }
        } else if (error.request) {
          error_message = 'server did not respond';
        }
        this.error = '<span class="red">Error removing institution<br>'+error_message+'</span>'
      }
    },
    move_inst_action: function(exp, inst) {
      if (this.remove_institution != '') {
        this.experiment = ''
        this.instutition = ''
        this.remove_institution = ''
      } else {
        this.experiment = exp
        this.instutition = ''
        this.remove_institution = inst
      }
    },
    leave_subgroup_action: async function(exp, inst, sub) {
      try {
        await keycloak.updateToken(5);
        const username = await get_username();
        let data = {}
        data[sub] = false
        for (const subgroup of this.experiments[exp][inst].subgroups) {
          if (sub != subgroup)
            data[subgroup] = true
        }
        const resp = await axios.put('/api/experiments/'+exp+'/institutions/'+inst+'/users/'+username, data, {
          headers: {'Authorization': 'bearer '+keycloak.token}
        });
        console.log('Response:')
        console.log(resp)
        this.refresh = this.refresh+1
      } catch (error) {
        console.log('error')
        console.log(error)
        let error_message = 'undefined error';
        if (error.response && 'data' in error.response) {
          if ('code' in error.response.data) {
            error_message = 'Code: '+error.response.data['code']+'<br>Message: '+error.response.data['error'];
          } else {
            error_message = JSON.stringify(error.response.data)
          }
        } else if (error.request) {
          error_message = 'server did not respond';
        }
        this.error = '<span class="red">Error leaving subgroup<br>'+error_message+'</span>'
      }
    },
    leave_group_action: async function(group_id) {
      try {
        await keycloak.updateToken(5);
        const username = await get_username();
        const resp = await axios.delete('/api/groups/'+group_id+'/'+username, {
          headers: {'Authorization': 'bearer '+keycloak.token}
        });
        console.log('Response:')
        console.log(resp)
        this.refresh = this.refresh+1
      } catch (error) {
        console.log('error')
        console.log(error)
        let error_message = 'undefined error';
        if (error.response && 'data' in error.response) {
          if ('code' in error.response.data) {
            error_message = 'Code: '+error.response.data['code']+'<br>Message: '+error.response.data['error'];
          } else {
            error_message = JSON.stringify(error.response.data)
          }
        } else if (error.request) {
          error_message = 'server did not respond';
        }
        this.error = '<span class="red">Error leaving group<br>'+error_message+'</span>'
      }
    }
  },
  template: `
<article class="home">
  <div v-if="keycloak.authenticated">
    <h2 style="margin-bottom: 1em">My profile:</h2>
    <div class="error_box" v-if="error" v-html="error"></div>
    <h3>Experiments / Institutions</h3>
    <div v-if="$asyncComputed.my_experiments.success">
      <div class="indent" v-for="(insts, exp) in my_experiments">
        <p class="italics">{{ exp }}<p>
        <div class="double_indent institution" v-for="(inst_data, inst) in insts">
          <span class="italics">{{ inst }}</span>
          <button @click="move_inst_action(exp, inst)">Move institutions</button>
          <button @click="leave_inst_action(exp, inst)">Leave institution</button>
          <div class="double_indent" v-if="remove_institution != ''" >
            <form class="newuser" @submit.prevent="submit">
              <div class="entry">
                <p>Select institution:</p>
                <select v-model="institution">
                  <option disabled value="">Please select one</option>
                  <option v-for="inst2 in institutions">{{ inst2 }}</option>
                </select>
                <span class="red" v-if="!validInstitution">invalid entry</span>
              </div>
              <div class="error_box" v-if="form_error" v-html="form_error"></div>
              <div class="entry">
                <input type="submit" value="Submit Move Request">
              </div>
            </form>
          </div>
          <div class="double_indent subgroup" v-for="sub in inst_data.subgroups">
            <span class="italics">{{ sub }}</span>
            <button @click="leave_subgroup_action(exp, inst, sub)">Leave sub-group</button>
          </div>
        </div>
      </div>
      <div class="indent" v-if="my_experiments.length <= 0">You do not belong to any institutions</div>
      <div class="join">
        <button @click="join_inst = !join_inst">Join an institution</button>
        <div class="double_indent" v-if="join_inst" >
          <form class="newuser" @submit.prevent="submit">
            <div class="entry">
              <p>Select experiment:</p>
              <select v-model="experiment">
                <option disabled value="">Please select one</option>
                <option v-for="(insts, exp) in experiments">{{ exp }}</option>
              </select>
              <span class="red" v-if="!valid && !validExperiment">invalid entry</span>
            </div>
            <div class="entry">
              <p>Select institution:</p>
              <select v-model="institution">
                <option disabled value="">Please select one</option>
                <option v-for="inst in institutions">{{ inst }}</option>
              </select>
              <span class="red" v-if="!valid && !validInstitution">invalid entry</span>
            </div>
            <div class="error_box" v-if="form_error" v-html="form_error"></div>
            <div class="entry" v-if="!submitted">
              <input type="submit" value="Submit Join Request">
            </div>
          </form>
        </div>
      </div>
    </div>
    <div class="indent" v-else>Loading institution information...</div>
    <h3>Groups</h3>
    <div v-if="$asyncComputed.my_groups.success">
      <div class="indent group" v-for="(grp_id,grp) in my_groups">
        <span class="italics">{{ grp }}</span>
        <button @click="leave_group_action(grp_id)">Leave group</button>
      </div>
      <div class="indent" v-if="my_groups.length <= 0">You do not belong to any groups</div>
    </div>
    <div class="indent" v-else>Loading group information...</div>
    <div class="join">
      <button @click="join_group = !join_group">Join a group</button>
      <div class="double_indent" v-if="join_group" >
        <form class="newuser" @submit.prevent="submit_group">
          <div class="entry">
            <p>Select group:</p>
            <select v-model="group">
              <option disabled value="">Please select one</option>
              <option v-for="(grp_id,grp) in groups">{{ grp }}</option>
            </select>
            <span class="red" v-if="!validGroup">invalid entry</span>
          </div>
          <div class="error_box" v-if="form_error" v-html="form_error"></div>
          <div class="entry">
            <input type="submit" value="Submit Join Request">
          </div>
        </form>
      </div>
    </div>
  </div>
  <div v-else>
    <h3>Welcome to the IceCube Neutrino Observatory identity management console.</h3>
    <p>Existing users should <span style="font-size: 150%"><login></login></span></p>
    <p>New users should ask their PI for a registration link.</p>
  </div>
</article>`
}

UserInfo = {
  data: function(){
    return {
      title: ''
    }
  },
  asyncComputed: {
    userinfo: async function() {
      if (!keycloak.authenticated)
        return {}
      try {
        var ret = await keycloak.loadUserInfo();
        return ret
      } catch (error) {
        return {"error": JSON.stringify(error)}
      }
    }
  },
  template: `
<article class="user-info">
  <h2>User details:</h2>
  <div v-for="(value, name) in userinfo">{{ name }}: {{ value }}</div>
</article>`
}

Register = {
  data: function(){
    return {
      experiment: '',
      institution: '',
      firstName: '',
      lastName: '',
      authorListName: '',
      email: '',
      valid: true,
      errMessage: '',
      submitted: false
    }
  },
  props: ['experiment', 'institution'],
  computed: {
    validFirstName: function() {
      return this.firstName
    },
    validLastName: function() {
      return this.lastName
    },
    validAuthorListName: function() {
      return this.authorListName
    },
    validEmail: function() {
      return this.email.indexOf('@',1) > 0
    }
  },
  asyncComputed: {
    validExperiment: function() {
      try {
        return this.experiment != '' && this.experiments !== null && this.experiment in this.experiments
      } catch(error) {
        return false
      }
    },
    validInstitution: function() {
      try {
        return this.institution != '' && this.experiments !== null && this.experiment in this.experiments && this.institution in this.experiments[this.experiment]
      } catch(error) {
        return false
      }
    },
    experiments: get_all_inst_subgroups
  },
  methods: {
      submit: async function(e) {
          // validate
          this.valid = (this.validExperiment && this.validInstitution && this.validFirstName
                  && this.validLastName && (!this.authorListName || this.validAuthorListName)
                  && this.validEmail)

          // now submit
          if (this.valid) {
              this.errMessage = 'Submission processing';
              try {
                  const resp = await axios.post('/api/inst_approvals', {
                      experiment: this.experiment,
                      institution: this.institution,
                      first_name: this.firstName,
                      last_name: this.lastName,
                      author_name: this.authorListName,
                      email: this.email
                  });
                  console.log('Response:')
                  console.log(resp)
                  this.errMessage = 'Submission successful'
                  this.submitted = true
              } catch (error) {
                  console.log('error')
                  console.log(error)
                  let error_message = 'undefined error';
                  if (error.response) {
                      if ('code' in error.response.data) {
                          error_message = 'Code: '+error.response.data['code']+'<br>Message: '+error.response.data['error'];
                      } else {
                          error_message = JSON.stringify(error.response.data)
                      }
                  } else if (error.request) {
                      error_message = 'server did not respond';
                  }
                  this.errMessage = '<span class="red">Error in submission<br>'+error_message+'</span>'
              }
          } else {
              this.errMessage = '<span class="red">Please fix invalid entries</span>'
          }
      }
  },
  template: `
<article class="register">
    <h2>Register a new account</h2>
    <form class="newuser" @submit.prevent="submit" v-if="$asyncComputed.experiments.success">
      <div class="entry">
        <span class="red">* entry is requred</span>
      </div>
      <div class="entry">
        <p>Select your experiment: <span class="red">*</span></p>
        <select v-model="experiment">
          <option disabled value="">Please select one</option>
          <option v-for="(insts, exp) in experiments">{{ exp }}</option>
        </select>
        <span class="red" v-if="!valid && !validExperiment">invalid entry</span>
      </div>
      <div class="entry">
        <p>Select your institution: <span class="red">*</span></p>
        <select v-model="institution">
          <option disabled value="">Please select one</option>
          <option v-for="(vals, inst) in experiments[experiment]">{{ inst }}</option>
        </select>
        <span class="red" v-if="!valid && !validInstitution">invalid entry</span>
      </div>
      <textinput name="First Name" inputName="first_name" v-model.trim="firstName"
       required=true :valid="validFirstName" :allValid="valid"></textinput>
      <textinput name="Last Name" inputName="last_name" v-model.trim="lastName"
       required=true :valid="validLastName" :allValid="valid"></textinput>
      <textinput name="Author List Name (usually abbreviated)" inputName="authorname"
       v-model.trim="authorListName" :valid="validAuthorListName" :allValid="valid"></textinput>
      <textinput name="Email Address" inputName="email" v-model.trim="email"
       required=true :valid="validEmail" :allValid="valid"></textinput>
      <div v-if="errMessage" class="error_box" v-html="errMessage"></div>
      <div class="entry" v-if="!submitted">
        <input type="submit" value="Submit Registration">
      </div>
    </form>
</article>`
}

Insts = {
  data: function(){
    return {
      refresh: 0,
      error: ''
    }
  },
  asyncComputed: {
    approvals: {
      get: async function() {
        try {
          await keycloak.updateToken(5);
          var ret = await axios.get('/api/inst_approvals', {
            headers: {'Authorization': 'bearer '+keycloak.token}
          })
          let institutions = {}
          for (const entry of ret['data']) {
            let inst = entry['experiment']+entry['institution']
            if (!(inst in institutions)) {
              institutions[inst] = {
                experiment: entry['experiment'],
                institution: entry['institution'],
                users: []
              }
            }
            institutions[inst]['users'].push(entry)
          }
          return Object.values(institutions)
        } catch (error) {
          this.error = "Error getting approvals: "+error['message']
          return []
        }
      },
      watch: ['refresh']
    },
    institutions: {
      get: async function() {
        try {
          const inst_admins = await get_my_inst_admins();
          let institutions = []
          for (const inst of inst_admins) {
            let parts = inst.split('/')
            await keycloak.updateToken(5);
            var ret = await axios.get('/api/experiments/'+parts[2]+'/institutions/'+parts[3]+'/users', {
              headers: {'Authorization': 'bearer '+keycloak.token}
            })
            let entry = {
              experiment: parts[2],
              institution: parts[3],
              members: {}
            }
            for (const key in ret.data) {
              entry.members[key] = ret.data[key]
            } 
            institutions.push(entry)
          }
          return institutions
        } catch (error) {
          this.error = "Error getting institutions: "+error['message']
          return []
        }
      },
      watch: ['refresh']
    }
  },
  methods: {
    approve: async function(approval_id) {
      try {
        await keycloak.updateToken(5);
        var token = keycloak.token;
        await axios.post('/api/inst_approvals/'+approval_id+'/actions/approve', {}, {
          headers: {'Authorization': 'bearer '+token}
        });
        this.error = ""
        this.refresh = this.refresh+1
      } catch (error) {
        this.error = "Error approving: "+error['message']
      }
    },
    deny: async function(approval_id) {
      try {
        await keycloak.updateToken(5);
        var token = keycloak.token;
        await axios.post('/api/inst_approvals/'+approval_id+'/actions/deny', {}, {
          headers: {'Authorization': 'bearer '+token}
        });
        this.error = ""
        this.refresh = this.refresh+1
      } catch (error) {
        this.error = "Error denying: "+error['message']
      }
    },
    add: async function(inst, name, username) {
      try {
        if (username == '') {
          this.error = "Error adding user: did not enter user name"
          return
        }
        await keycloak.updateToken(5);
        var token = keycloak.token;
        let data = {}
        for (const key in inst.members) {
          if (key == 'users')
            continue
          if (name == key) {
            data[key] = true
          } else if (inst.members[key].includes(username)) {
            data[key] = true
          }
        }
        await axios.put('/api/experiments/'+inst.experiment+'/institutions/'+inst.institution+'/users/'+username, data, {
          headers: {'Authorization': 'bearer '+keycloak.token}
        })
        this.error = ""
        this.refresh = this.refresh+1
      } catch (error) {
        this.error = "Error adding user: "+error['message']
      }
    },
    remove: async function(inst, name, username) {
      try {
        await keycloak.updateToken(5);
        var token = keycloak.token;
        if (name == 'users') {
          await axios.delete('/api/experiments/'+inst.experiment+'/institutions/'+inst.institution+'/users/'+username, {
            headers: {'Authorization': 'bearer '+keycloak.token}
          })
        } else {
          let data = {}
          for (const key in inst.members) {
            if (key == 'users')
              continue
            if (name == key) {
              data[key] = false
            } else if (inst.members[key].includes(username)) {
              data[key] = true
            }
          }
          await axios.put('/api/experiments/'+inst.experiment+'/institutions/'+inst.institution+'/users/'+username, data, {
            headers: {'Authorization': 'bearer '+keycloak.token}
          })
        }
        this.error = ""
        this.refresh = this.refresh+1
      } catch (error) {
        this.error = "Error removing user: "+error['message']
      }
    }
  },
  template: `
<article class="institutions">
  <div class="error_box red" v-if="error">{{ error }}</div>
  <div v-if="$asyncComputed.approvals.success">
    <h3>Users needing approval:</h3>
    <div v-if="approvals.length > 0" class="indent">
      <div class="inst" v-for="inst in approvals">
        <h4>{{ inst["experiment"] }} - {{ inst["institution"] }}</h4>
        <div class="user indent" v-for="approval in inst['users']">
          <span class="newuser" v-if="'newuser' in approval">New</span> 
          <span class="username">{{ approval['username'] }}</span>
          <span class="name" v-if="'first_name' in approval">{{ approval['first_name'] }} {{ approval['last_name'] }}</span>
          <span class="author" v-if="'authorlist' in approval">Author</span>
          <button @click="approve(approval['id'])">Approve</button>
          <button @click="deny(approval['id'])">Deny</button>
        </div>
      </div>
    </div>
    <div v-else class="indent">No approvals waiting</div>
  </div>
  <div v-if="$asyncComputed.institutions.success">
    <h3>Administered institutions:</h3>
    <div class="inst" v-for="inst in institutions">
      <h4>{{ inst.experiment }} - {{ inst.institution }}</h4>
      <div class="indent" v-for="(members, name) in inst.members">
        <p>{{ name }}</p>
        <div class="double_indent" v-if="members.length > 0">
          <div class="user" v-for="user in members">
            <span class="username">{{ user }}</span>
            <button @click="remove(inst, name, user)">Remove</button>
          </div>
        </div>
        <div class="double_indent" v-else>No members</div>
        <div class="double_indent add">
          <addinstuser :addFunc="add" :inst="inst" :name="name"></addinstuser>
        </div>
      </div>
    </div>
  </div>
</article>`
}

Groups = {
  data: function(){
    return {
      refresh: 0,
      error: ''
    }
  },
  asyncComputed: {
    approvals: {
      get: async function() {
        try {
          await keycloak.updateToken(5);
          var ret = await axios.get('/api/group_approvals', {
            headers: {'Authorization': 'bearer '+keycloak.token}
          })
          let groups = {}
          for (const entry of ret['data']) {
            let group = entry['group']
            if (!(group in groups)) {
              groups[group] = {
                id: entry['group_id'],
                name: group,
                members: []
              }
            }
            groups[group]['members'].push(entry)
          }
          return Object.values(groups)
        } catch (error) {
          this.error = "Error getting approvals: "+error['message']
          return []
        }
      },
      watch: ['refresh']
    },
    groups: {
      get: async function() {
        try {
          const group_admins = await get_my_group_admins();
          let ret = await axios.get('/api/groups', {
            headers: {'Authorization': 'bearer '+keycloak.token}
          })
          const all_groups = ret.data;
          let groups = []
          for (const group of group_admins) {
            if (group in all_groups) {
              await keycloak.updateToken(5);
              let ret = await axios.get('/api/groups/'+all_groups[group], {
                headers: {'Authorization': 'bearer '+keycloak.token}
              })
              let entry = {
                id: all_groups[group],
                name: group,
                members: ret.data
              }
              groups.push(entry)
            }
          }
          return groups
        } catch (error) {
          this.error = "Error getting groups: "+error['message']
          return []
        }
      },
      watch: ['refresh']
    }
  },
  methods: {
    approve: async function(approval_id) {
      try {
        await keycloak.updateToken(5);
        var token = keycloak.token;
        await axios.post('/api/group_approvals/'+approval_id+'/actions/approve', {}, {
          headers: {'Authorization': 'bearer '+token}
        });
        this.error = ""
        this.refresh = this.refresh+1
      } catch (error) {
        this.error = "Error approving: "+error['message']
      }
    },
    deny: async function(approval_id) {
      try {
        await keycloak.updateToken(5);
        var token = keycloak.token;
        await axios.post('/api/group_approvals/'+approval_id+'/actions/deny', {}, {
          headers: {'Authorization': 'bearer '+token}
        });
        this.error = ""
        this.refresh = this.refresh+1
      } catch (error) {
        this.error = "Error denying: "+error['message']
      }
    },
    add: async function(group_id, username) {
      try {
        if (username == '') {
          this.error = "Error adding user: did not enter user name"
          return
        }
        await keycloak.updateToken(5);
        var token = keycloak.token;
        await axios.put('/api/groups/'+group_id+'/'+username, {}, {
          headers: {'Authorization': 'bearer '+keycloak.token}
        })
        this.error = ""
        this.refresh = this.refresh+1
      } catch (error) {
        this.error = "Error adding user: "+error['message']
      }
    },
    remove: async function(group_id, username) {
      try {
        await keycloak.updateToken(5);
        var token = keycloak.token;
        await axios.delete('/api/groups/'+group_id+'/'+username, {
          headers: {'Authorization': 'bearer '+keycloak.token}
        })
        this.error = ""
        this.refresh = this.refresh+1
      } catch (error) {
        this.error = "Error removing user: "+error['message']
      }
    }
  },
  template: `
<article class="groups">
  <div class="error_box red" v-if="error">{{ error }}</div>
  <div v-if="$asyncComputed.approvals.success">
    <h3>Users needing approval:</h3>
    <div v-if="approvals.length > 0" class="indent">
      <div class="group" v-for="group in approvals">
        <h4>{{ group["name"] }}</h4>
        <div class="user indent" v-for="approval in group['members']">
          <span class="username">{{ approval['username'] }}</span>
          <span class="name" v-if="'first_name' in approval">{{ approval['first_name'] }} {{ approval['last_name'] }}</span>
          <button @click="approve(approval['id'])">Approve</button>
          <button @click="deny(approval['id'])">Deny</button>
        </div>
      </div>
    </div>
    <div v-else class="indent">No approvals waiting</div>
  </div>
  <div v-if="$asyncComputed.groups.success">
    <h3>Administered groups:</h3>
    <div class="group" v-for="group in groups">
      <p>{{ group["name"] }}</p>
      <div class="double_indent" v-if="group['members'].length > 0">
        <div class="user" v-for="user in group['members']">
          <span class="username">{{ user }}</span>
          <button @click="remove(group['id'], user)">Remove</button>
        </div>
      </div>
      <div class="double_indent" v-else>No members</div>
      <div class="double_indent add">
        <addgroupuser :addFunc="add" :group="group['id']"></addgroupuser>
      </div>
    </div>
  </div>
</article>`
}


Error404 = {
    data: function(){
        return {
        }
    },
    computed: {
        'pathMatch': function() {
            return this.$route.params[0];
        }
    },
    template: `
<article class="error">
    <h2>Error: page not found</h2>
    <p><span class="code">{{ pathMatch }}</span> does not exist</p>
</article>`
}


/** Vue components **/

Vue.component('textinput', {
  data: function(){
    return {
      required: false,
      valid: true,
      allValid: true
    }
  },
  props: ['name', 'inputName', 'value', 'required', 'valid', 'allValid'],
  template: `
<div class="entry">
  <p>{{ name }}: <span v-if="required" class="red">*</span></p>
  <input :name="inputName" :value="value" @input="$emit('input', $event.target.value)">
  <span class="red" v-if="!allValid && !valid && (required || value)">invalid entry</span>
</div>`
})

Vue.component('addinstuser', {
  data: function(){
    return {
      addFunc: null,
      inst: null,
      name: '',
      username: ''
    }
  },
  props: ['addFunc', 'inst', 'name'],
  methods: {
    submit: function() {
      this.addFunc(this.inst, this.name, this.username)
    }
  },
  template: `
<div>
  Add user: <input v-model.trim="username" placeholder="username" @input="$emit('input', $event.target.value)" @keyup.enter="submit">
  <button @click="submit">Add</button>
</div>`
})

Vue.component('addgroupuser', {
  data: function(){
    return {
      addFunc: null,
      group: '',
      username: ''
    }
  },
  props: ['addFunc', 'group'],
  methods: {
    submit: function() {
      this.addFunc(this.group, this.username)
    }
  },
  template: `
<div>
  Add user: <input v-model.trim="username" placeholder="username" @input="$emit('input', $event.target.value)" @keyup.enter="submit">
  <button @click="submit">Add</button>
</div>`
})

Vue.component('navpage', {
  data: function(){
    return {
      path: '',
      name: '',
      current: ''
    }
  },
  props: ['path', 'name', 'current'],
  computed: {
    classObj: function() {
      return {
        active: this.name == this.current
      }
    },
  },
  beforeRouteEnter(to, from, next) {
    this.current = to.params.route
    next()
  },
  template: '<li :class="classObj"><router-link :to="path">{{ name }}</router-link></li>'
});

Vue.component('account', {
  data: function(){
    return {
    }
  },
  asyncComputed: {
    name: async function() {
      if (!keycloak.authenticated)
        return ""
      try {
        var ret = await keycloak.loadUserInfo();
        return ret['given_name']
      } catch (error) {
        return ""
      }
    }
  },
  methods: {
    logout: async function() {
      await keycloak.logout({redirectUri:window.location.origin})
    }
  },
  template: `
<div class="account">
  <login v-if="!keycloak.authenticated" caps="true"></login>
  <div v-else>Signed in as <span class="username">{{ name }}</span><br><logout caps="true"></logout></div>
</div>`
});

Vue.component('login', {
  data: function(){
    return {
      caps: "true",
    }
  },
  props: ['caps'],
  computed: {
    name: function() {
      if (this.caps == "true")
        return 'Sign in'
      else
        return 'sign in'
    }
  },
  methods: {
    login: async function() {
      await keycloak.login({redirectUri:window.location})
    }
  },
  template: `<span class="login-link" @click="login">{{ name }}</span>`
});

Vue.component('logout', {
  data: function(){
    return {
      caps: false,
    }
  },
  props: ['caps'],
  computed: {
    name: function() {
      if (this.caps)
        return 'Sign out'
      else
        return 'sign out'
    }
  },
  methods: {
    logout: async function() {
      await keycloak.logout({redirectUri:window.location.origin})
    }
  },
  template: `<span class="login-link" @click="logout">{{ name }}</span>`
});


// scrollBehavior:
// - only available in html5 history mode
// - defaults to no scroll behavior
// - return false to prevent scroll
const scrollBehavior = function (to, from, savedPosition) {
  if (savedPosition) {
    // savedPosition is only available for popstate navigations.
    return savedPosition
  } else {
    const position = {}

    // scroll to anchor by returning the selector
    if (to.hash) {
      position.selector = to.hash

      // specify offset of the element
      if (to.hash === '#anchor2') {
        position.offset = { y: 100 }
      }

      // bypass #1number check
      if (/^#\d/.test(to.hash) || document.querySelector(to.hash)) {
        return position
      }

      // if the returned position is falsy or an empty object,
      // will retain current scroll position.
      return false
    }

    return new Promise(resolve => {
      // check if any matched route config has meta that requires scrolling to top
      if (to.matched.some(m => m.meta.scrollToTop)) {
        // coords will be used if no selector is provided,
        // or if the selector didn't match any element.
        position.x = 0
        position.y = 0
      }

      // wait for the out transition to complete (if necessary)
      this.app.$root.$once('triggerScroll', () => {
        // if the resolved position is falsy or an empty object,
        // will retain current scroll position.
        resolve(position)
      })
    })
  }
}


var routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/userinfo', name: 'userinfo', component: UserInfo,
    meta: { requiresAuth: true, testing: true }
  },
  { path: '/register', name: 'register', component: Register,
    props: (route) => ({
      experiment: route.query.experiment,
      institution: route.query.institution
    })
  },
  { path: '/institutions', name: 'Institutions', component: Insts,
    meta: { requiresAuth: true, requiresInstAdmin: true }
  },
  { path: '/groups', name: 'Groups', component: Groups,
    meta: { requiresAuth: true, requiresGroupAdmin: true }
  },
  { path: '*', name: '404', component: Error404, props: true }
];

async function vue_startup(keycloak_url, keycloak_realm){
  keycloak = new Keycloak({
    url: keycloak_url+'/auth',
    realm: keycloak_realm,
    clientId: 'user_mgmt'
  });
  try {
    await keycloak.init();
  } catch (error) {
    console.log("error initializing keycloak")
  }

  var router = new VueRouter({
    mode: 'history',
    routes: routes,
    scrollBehavior: scrollBehavior
  })
  router.beforeEach(async function(to, from, next){
    console.log('baseurl: '+window.location.origin)

    if (to.meta && to.meta.requiresAuth && !keycloak.authenticated) {
      // do login process
      console.log("keycloak needs login")
      await keycloak.login({redirectUri:window.location.origin+to.path})
    }
    else next()
  })

  var app = new Vue({
    el: '#page-container',
    data: {
      routes: routes,
      current: 'home'
    },
    router: router,
    asyncComputed: {
      visibleRoutes: async function() {
        var current = this.current;
        var ret = []
        for (const r of this.routes) {
          if (r.path[0] == '*')
            continue
          if (r.path.startsWith('/register') && current != 'register')
            continue
          if (krs_debug !== true && r.meta && r.meta.testing)
            continue
          if (r.meta && r.meta.requiresAuth && !keycloak.authenticated)
            continue
          if (r.meta && r.meta.requiresInstAdmin && (await get_my_inst_admins()).length <= 0)
            continue
          if (r.meta && r.meta.requiresGroupAdmin && (await get_my_group_admins()).length <= 0)
            continue
          ret.push(r)
        }
        return ret
      }
    },
    watch: {
      '$route.currentRoute.path': {
        handler: function() {
          console.log('currentPath update:'+router.currentRoute.path)
          this.current = router.currentRoute.name
        },
        deep: true,
        immediate: true,
      }
    }
  })
}
