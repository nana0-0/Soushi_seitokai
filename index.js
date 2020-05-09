new Vue({
    el: '#app',
    vuetify: new Vuetify(),
    data: {
        items: [],
        show1: false,
        password: "",
        loggedin: false,
        session: "",
        errormsg: "",
        messages: [],
        btn_disable: true
    },
    created: function () {
        this.items.push("items3")
    },
    methods: {
        login: function () {
            console.log("clicked")
            const obj = { "password": this.password }
            const body = Object.keys(obj).reduce((o, key) => (o.set(key, obj[key]), o), new FormData());
            fetch("/api/session", {
                method: "POST", // *GET, POST, PUT, DELETE, etc
                redirect: "follow", // manual, *follow, error
                body, // 本文のデータ型は "Content-Type" ヘッダーと一致する必要があります
            })
                .then(response => response.json())
                .then(d => {
                    console.log(d)
                    if (d.status !== "ok") {
                        this.errormsg = d.error
                        return
                    }

                    this.loggedin = true
                    this.session = d.session
                    this.errormsg = ""
                    this.messages = Array(this.session.length).fill("")

                    fetch("/api/suggestions?session=" + this.session)
                        .then(d => d.json())
                        .then(d => {
                            console.log(d)
                            this.items = d.data
                            this.btn_disable = false
                        })
                });
        },
        reply: function (index, userid, text, uuid) {
            this.btn_disable = true
            console.log("clicked")
            const obj = { "session": this.session, content: text, userid, uuid }
            const body = Object.keys(obj).reduce((o, key) => (o.set(key, obj[key]), o), new FormData());
            fetch("/api/reply", {
                method: "POST", // *GET, POST, PUT, DELETE, etc.
                redirect: "follow", // manual, *follow, error
                body, // 本文のデータ型は "Content-Type" ヘッダーと一致する必要があります
            })
                .then(response => response.json())
                .then(d => {
                    console.log(d)
                    this.login()
                })
                .catch(() => { btn_disable = false });
        }
    }
})