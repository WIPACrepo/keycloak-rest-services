// debug flag
var krs_debug = true;

// global Keycloak object
var keycloak;


/** helper functions **/

var get_my_experiments = async function() {
  if (!keycloak.authenticated)
    return []
  try {
    if (keycloak.isTokenExpired(5))
      await keycloak.updateToken(60)
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
    if (keycloak.isTokenExpired(5))
      await keycloak.updateToken(60)
    let institutions = []
    for (const group of keycloak.tokenParsed.groups) {
      if (group.startsWith('/institutions')) {
        const parts = group.split('/')
        if (parts.length == 4 && parts[2] == experiment) {
          const inst = parts[3]
          if (!institutions.includes(inst))
            institutions.push(inst)
        }
      }
    }
    console.log("get_my_institutions() - "+JSON.stringify(institutions))
    return institutions
  } catch (error) {
    console.log("error getting institutions from token")
    return []
  }
};

var get_my_inst_admins = async function() {
  if (!keycloak.authenticated)
    return []
  try {
    if (keycloak.isTokenExpired(5))
      await keycloak.updateToken(60)
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
    if (keycloak.isTokenExpired(5))
      await keycloak.updateToken(60)
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
    return groups
  } catch (error) {
    console.log("error getting admin groups from token")
    return []
  }
};


/** Routes **/

Home = {
  data: function(){
    return {
      error: ''
    }
  },
  asyncComputed: {
    experiments: async function(){
      let exps = await get_my_experiments()
      let ret = {};
      for (const exp of exps) {
        ret[exp] = await get_my_institutions(exp)
      }
      return ret
    },
    groups: async function(){
      return []
    }
  },
  template: `
<article class="home">
  <div v-if="keycloak.authenticated">
    <h2 style="margin-bottom: 1em">My profile:</h2>
    <div class="error_box" v-if="error">{{ error }}</div>
    <h3>Experiments / Institutions</h3>
    <div class="indent" v-for="(institutions, exp) in experiments">
      <p class="experiment">{{ exp }}<p>
      <div class="double_indent" v-for="inst in institutions">
        <span class="institution">{{ inst }}</span>
      </div>
    </div>
    <div class="indent" v-if="experiments.length <= 0">You do not belong to any institutions</div>
    <h3>Groups</h3>
    <div class="indent" v-for="group in groups">
      <span class="group">{{ group }}</span>
    </div>
    <div class="indent" v-if="groups.length <= 0">You do not belong to any groups</div>
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
        return this.experiment != '' && this.experiments !== null && this.experiments.includes(this.experiment)
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
    experiments: async function() {
      try {
        const resp = await axios.get('/api/experiments');
        console.log('Response:')
        console.log(resp)
        return resp.data
      } catch (error) {
        console.log('error')
        console.log(error)
      }
      return {}
    },
    institutions: async function() {
      if (this.validExperiment) {
        try {
          const resp = await axios.get('/api/experiments/'+this.experiment+'/institutions');
          console.log('Response:')
          console.log(resp)
          return resp.data
        } catch (error) {
          console.log('error')
          console.log(error)
        }
      }
      return {}
    }
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
    <form class="newuser" @submit.prevent="submit">
      <div class="entry">
        <span class="red">* entry is requred</span>
      </div>
      <div class="entry">
        <p>Select your experiment: <span class="red">*</span></p>
        <select v-model="experiment">
          <option disabled value="">Please select one</option>
          <option v-for="exp in experiments">{{ exp }}</option>
        </select>
        <span class="red" v-if="!valid && !validExperiment">invalid entry</span>
      </div>
      <div class="entry">
        <p>Select your institution: <span class="red">*</span></p>
        <select v-model="institution">
          <option disabled value="">Please select one</option>
          <option v-for="inst in institutions">{{ inst }}</option>
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

InstMove = {
  data: function(){
    return {
      experiment: '',
      remove_institution: '',
      institution: '',
      valid: true,
      errMessage: '',
      submitted: false
    }
  },
  asyncComputed: {
    validExperiment: function() {
      try {
        return this.experiment != '' && this.experiments !== null && this.experiments.includes(this.experiment)
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
    experiments: async function() {
      return await get_my_experiments()
    },
    institutions: async function() {
      if (this.validExperiment) {
        try {
          const resp = await axios.get('/api/experiments/'+this.experiment+'/institutions');
          console.log('Response:')
          console.log(resp)
          return resp.data
        } catch (error) {
          console.log('error')
          console.log(error)
        }
      }
      return {}
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
                  if (!keycloak.authenticated)
                    throw "not authenticated"
                  if (keycloak.isTokenExpired(5))
                    await keycloak.updateToken(60)
                  const resp = await axios.post('/api/inst_approvals', {
                      experiment: this.experiment,
                      institution: this.institution,
                      remove_institution: this.remove_institution
                  }, {
                    headers: {'Authorization': 'bearer '+keycloak.token}
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
    <h2>Move institution</h2>
    <form class="newuser" @submit.prevent="submit">
      <div class="entry">
        <span class="red">* entry is requred</span>
      </div>
      <div class="entry">
        <p>Select your experiment: <span class="red">*</span></p>
        <select v-model="experiment">
          <option disabled value="">Please select one</option>
          <option v-for="exp in experiments">{{ exp }}</option>
        </select>
        <span class="red" v-if="!valid && !validExperiment">invalid entry</span>
      </div>
      <div class="entry">
        <p>Select new institution: <span class="red">*</span></p>
        <select v-model="institution">
          <option disabled value="">Please select one</option>
          <option v-for="inst in institutions">{{ inst }}</option>
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

InstApproval = {
  data: function(){
    return {
      approval_data: null,
      error: ''
    }
  },
  asyncComputed: {
    approvals: async function() {
      try {
        if (this.approval_data===null) {
          await this.get_approval_data()
        }
        var institutions = {};
        for (const approval_id in this.approval_data) {
          let entry = this.approval_data[approval_id];
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
    }
  },
  methods: {
    get_approval_data: async function() {
      try {
        await keycloak.updateToken(60);
        var token = keycloak.token;
        var ret = await axios.get('/api/inst_approvals', {
          headers: {'Authorization': 'bearer '+token}
        });
        this.approval_data = {}
        for (let i=0;i<ret['data'].length;i++){
          let entry = ret['data'][i];
          this.approval_data[entry['approval_id']] = entry
        }
      } catch (error) {
        this.error = "Error getting approvals: "+error['message']
      }
    },
    approve: async function(approval_id) {
      try {
        await keycloak.updateToken(60);
        var token = keycloak.token;
        await axios.post('/api/inst_approvals/'+approval_id+'/actions/approve', {}, {
          headers: {'Authorization': 'bearer '+token}
        });
        this.remove(approval_id)
        this.error = ""
      } catch (error) {
        this.error = "Error approving: "+error['message']
      }
    },
    deny: async function(approval_id) {
      try {
        await keycloak.updateToken(60);
        var token = keycloak.token;
        await axios.post('/api/inst_approvals/'+approval_id+'/actions/deny', {}, {
          headers: {'Authorization': 'bearer '+token}
        });
        this.remove(approval_id)
        this.error = ""
      } catch (error) {
        this.error = "Error denying: "+error['message']
      }
    },
    remove: function(approval_id) {
      let new_approval_data = {}
      let old_approval_data = Object.values(this.approval_data);
      for (const entry of old_approval_data) {
        if (entry['id'] != approval_id)
          new_approval_data[entry['id']] = entry
      }
      this.approval_data = new_approval_data
    }
  },
  template: `
<article class="inst-approvals">
  <h2>Users needing approval:</h2>
  <div class="error_box red" v-if="error">{{ error }}</div>
  <div class="inst" v-for="inst in approvals">
    <h4>{{ inst["experiment"] }} - {{ inst["institution"] }}</h4>
    <div class="user" v-for="approval in inst['users']">
      <span class="username">{{ approval['username'] }}</span>
      <button @click="approve(approval['id'])">Approve</button>
      <button @click="deny(approval['id'])">Deny</button>
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
  { path: '/instApproval', name: 'Inst Approvals', component: InstApproval,
    meta: { requiresAuth: true, requiresInstAdmin: true }
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

    if ('requiresAuth' in to.meta && to.meta['requiresAuth'] && !keycloak.authenticated) {
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
    computed: {
      visibleRoutes: function() {
        var current = this.current;
        return this.routes.filter(function (r) {
          if (r.path[0] == '*')
            return false
          if (r.path.startsWith('/register') && current != 'register')
            return false
          if ((!krs_debug) && r.meta.testing)
            return false
          if (r.meta && r.meta.requiresAuth && !keycloak.authenticated)
            return false
          if (r.meta && r.meta.requiresInstAdmin && get_my_inst_admins().length <= 0)
            return false
          if (r.meta && r.meta.requiresGroupAdmin && get_my_group_admins().length <= 0)
            return false
          return true
        })
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
