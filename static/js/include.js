document.addEventListener("DOMContentLoaded", function (e) {
    //Getting include attribute value
    let includes = document.getElementsByTagName("include");
    for (var i = 0; i < includes.length; i++) {
        let include = includes[i];

        //Loading include src value
        load_file(includes[i].attributes.src.value, function (text) {
            include.insertAdjacentHTML("afterend", text);
            include.remove();
        });
    }
    function load_file(filename, callback) {
        fetch(filename)
            .then((response) => response.text())
            .then((text) => callback(text));
    }
});
