var app = angular.module('myApp', []);
app.controller('formCtrl', function($scope,$http) {
    const api_base_url ="https://api.covidcitizens.org/api/v1/leadbyquery?";
    $scope.dataFetched=false;
    $scope.master = {city:{city:"Surat"}, resource:{type:"Plasma"}};
    $scope.cityList = [
        {city : "Mumbai"},
        {city : "Delhi"},
        {city : "Banglore"},
        {city : "Pune"},
        {city : "Lucknow"},
        {city : "Surat"}
    ];

    $scope.resourceList = [
        {type : "Ambulance"},
        {type : "Plasma"},
        {type : "Hospital"},
        {type : "Oxygen"}
    ];

    $scope.bloodGroup = [
        {type : "ap"},
        {type : "an"},
        {type : "bp"},
        {type : "bn"}
    ];

    // $scope.dataFormat=
    // [
    //     "location","contact_type","category","uuid","source","name","phone","lastverified"
    // ]

    $scope.fetch = function(data){
        url = api_base_url+"category="+data.resource.type+"&location="+data.city.city;
        console.log("URL:  "+ url);
        $http.get(url).then(function (response) {
            $scope.leads = response.data;
            console.log(response.data);
            console.log($scope.leads.data);
        });
        $scope.dataFetched=true;
    }
    
    $scope.reset = function() {
        $scope.filter = angular.copy($scope.master);
        $scope.fetch($scope.master);
    };
    $scope.reset();



    $scope.submit = function() {
        $scope.fetch($scope.filter);
    };
});

