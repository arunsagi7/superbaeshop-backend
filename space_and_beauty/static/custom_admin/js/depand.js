var master_data = []
var country = []
var states = []
var district = []
var religion = []
var caste = []
var sub_caste = []


var star = []
var degrees = []


$.ajax({
    url : '/category',
    type : 'GET',
    success : function(data) {
        master_data = data;

        country_selected =$('#id_country').val();

        state_selected = $('#id_state').val();
        district_selected = $('#id_district').val();
        cities_selected = $('#id_city').val();
        star_selected = $('#id_religion_details-0-star').val()
        raasi_selected = $('#id_religion_details-0-raasi').val()

        religion_selected = $('#id_religion_details-0-religion').val()
        caste_selected = $('#id_religion_details-0-caste').val()
        sub_caste_selected = $('#id_religion_details-0-sub_caste').val()


        dosham_selected =$('#id_user_details-0-dosham').val();

        if(!country_selected==""){
            country_change(country_selected)
            state_change(state_selected)
            district_change(district_selected)
        }else{
            append_select('id_country', master_data.country);
        }


        $(`#id_state option[value=${state_selected}]`).attr('selected','selected');
        $(`#id_district option[value=${district_selected}]`).attr('selected','selected');
        $(`#id_city option[value=${cities_selected}]`).attr('selected','selected');

        if(!religion_selected==""){
            religion_changed(religion_selected);
            caste_changed(caste_selected)
        }else{
            append_select('id_religion_details-0-religion', master_data.religions);
        }

        $(`#id_religion_details-0-caste option[value=${caste_selected}]`).attr('selected','selected');
        $(`#id_religion_details-0-sub_caste option[value=${sub_caste_selected}]`).attr('selected','selected');

        if(!star_selected==""){
            star_changed(star_selected);
            $(`#id_religion_details-0-raasi option[value=${raasi_selected}]`).attr('selected','selected');
        }

        append_select('id_user_details-0-dosham', master_data.dosham);

        append_select('id_education_details-0-degree', master_data.degrees);
    },
    error : function(request,error)
    {
        alert("Request: "+JSON.stringify(request));
    }
});

function country_change(val){
    $('#id_state').empty();
    $('#id_district').empty();
    $('#id_city').empty();

    country = master_data.country.filter(x => x.id === parseInt(val))[0]
    append_select('id_state', country.states);
}


function state_change(val){
    $('#id_district').empty();
    $('#id_city').empty();
    states = country.states.filter(x => x.id === parseInt(val))[0]
    append_select('id_district', states.district);
    append_select('dropdown-_district', states.district);
}

function district_change(val){
    $('#id_city').empty();
    district = states.district.filter(x => x.id === parseInt(val))[0]
    append_select('id_city', district.cities);
}

function religion_changed(val){
    $('#id_religion_details-0-caste').empty()
    $('#id_religion_details-0-sub_caste').empty()
    religion = master_data.religions.filter(x => x.id === parseInt(val))[0]
    append_select('id_religion_details-0-caste', religion.castes)
}

function caste_changed(val){
    $('#id_religion_details-0-sub_caste').empty()
    castes = religion.castes.filter(x => x.id === parseInt(val))[0]
    append_select('id_religion_details-0-sub_caste', castes.sub_castes)
}

function star_changed(val){
    $('#id_religion_details-0-raasi').empty()
    star = master_data.stars.filter(x => x.id === parseInt(val))[0]
    append_select('id_religion_details-0-raasi', star.raasi)
}

function degree_changed(val){
    $('#id_education_details-0-courses').empty()
    degrees = master_data.degrees.filter(x => x.id === parseInt(val))[0]
    append_select('id_education_details-0-courses', degrees.courses)
}

$('#id_country').on('change', function() {
    country_change(this.value)
});


$('#id_state').on('change', function() {
    state_change(this.value)
});

$('#id_district').on('change', function() {
    district_change(this.value)
});



$('#id_religion_details-0-religion').on('change', function() {
    religion_changed(this.value)
});


$('#id_religion_details-0-caste').on('change', function() {
    caste_changed(this.value)
});


$('#id_religion_details-0-star').on('change', function() {
    star_changed(this.value)
});


$('#id_education_details-0-degree').on('change', function() {
    degree_changed(this.value)
});

