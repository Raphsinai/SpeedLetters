function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
async function hamclick() {
    $("#hamburger").toggleClass('change');
    $("#clicknav").toggleClass('close');
    if ($("#clicknav").hasClass('open')) { await sleep(300) };
    $("#clicknav").toggle();
    $("#clicknav").toggleClass('open');
}