var app = angular.module('srcApp', []);
app.controller('srcCtrl', function ($scope) {
    $scope.sources = [
        {
            'url': 'https://www.volunteerscovihelp.org',
            'name': 'Volunteers.CoviHelp'
        },
        {
            'url': 'https://covidcitizens.org',
            'name': 'Covid Citizens'
        },
        {
            'url': 'https://www.covidfightclub.org',
            'name': 'Covid Fight Club'
        },
        {
            'url': 'https://www.covidindiaresources.com',
            'name': 'Covid India Resources'
        },
        {
            'url': 'https://covidwin.in',
            'name': 'Covid Win'
        },
        {
            'url': 'https://liferesources.in',
            'name': 'LifeResources'
        },
        {
            'url': 'http://dashboard.covid19.ap.gov.in/ims/hospbed_reports',
            'name': 'COVID 19 Andhra Pradesh'
        },
        {
            'url': 'https://coronabeds.jantasamvad.org/index.html',
            'name': 'COVID-19 Delhi Government'
        },
        {
            'url': 'https://www.justdial.com/verticals/Coronavirus-India/Resources',
            'name': 'Justdial COVID 19 Resources'
        },
        {
            'url': 'https://www.divcommpunecovid.com/ccsbeddashboard/hsr',
            'name': 'COVID CARE SOFTWARE - PUNE DIVISION'
        },
        {
            'url': 'https://stopcorona.tn.gov.in/beds.php',
            'name': 'Health & Family Welfare Department Government of Tamil Nadu'
        },
        {
            'url': 'https://twitter.com',
            'name': 'Twitter'
        }
    ];
});
