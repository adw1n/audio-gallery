/*
needed variables:
LEFT_IMG_MARGIN float
RIGHT_IMG_MARGIN float
TOP_IMG_MARGIN float
BOTTOM_IMG_MARGIN float

WAVEFORM_LINK string
SPECTRUM_LINK string

WAV_AUDIO_LINK string
MP3_AUDIO_LINK string

SPECTRUM_FFT_SIZE int
SPECTROGRAM_IMAGE_WIDTH int
SPECTROGRAM_IMAGE_HEIGHT int
*/


function set_up_enquire() {
    /*
    TODO parametrize this
    550 is the width of the spectrum (547, but you get the idea)
    once the screen width is less than 550 spectrum is going to be scaled using the chart plugin
    we can't use the chart plugin to enlarge the spectrum because of the tremendous loss of quality
    */
    enquire.register("screen and (max-width: 550px)", { //canvas width
        match : function() {
            $("#spectrum_chart").addClass("chart");
        },
        unmatch : function() {
            $("#spectrum_chart").removeClass("chart");
        }
    });
}

function getMaxOfArray(numArray) {
    /*
        Math.max(...array) is not supported on android browser
    */
    return Math.max.apply(null, numArray);
}

// used to refresh waveform and spectrogram every x seconds
// http://cai.zone/2013/07/a-quick-javascript-hack-to-fake-adjustin-html5-audio-elements-timeupdate-event-frequency/
var audio_clock;


var wavesurfer;
// supported by chrome, mobile chrome (Android), chromium, FF, Opera
// not supported by: IE, Safari, mobile android browser
var browserSupportsAudioApiAnalyserNode=false;

var audio; //the audio element with the music file
var analyser; // audio element analyzer
var context; // audio element context

var SPECTROGRAM_IMG;
var SPECTROGRAM_CURSOR; // the cursor that is drawn on top of the spectrogram

var spectrum_for_whole_audio_track; //json data  - array of fftSize/2+1 elements with float values
var spectrum_canvas_context;

//spectrum image gradient
var gradient;
function create_gradient() {
    gradient = spectrum_canvas_context.createLinearGradient(0,0,0,200);
    gradient.addColorStop(1,'#000000');
    gradient.addColorStop(0.75,'#ff0000');
    gradient.addColorStop(0.25,'#ffff00');
    gradient.addColorStop(0,'#ffffff');
}

var timelineInitialized=0;
function drawWaveformLegend(){
    /*
    draws (or refreshes - recalculates the size of the legend) 1,0,-1 values on the x axis of the waveform
    waveform's y axis is taken care by a plugin
     */
    var spectrogram_width=SPECTROGRAM_IMG.width();
    var waveformLegend=$("#waveform-legend");
    var left_margin=LEFT_IMG_MARGIN*spectrogram_width/SPECTROGRAM_IMAGE_WIDTH;
    waveformLegend.css({"left":-left_margin+"px","width":left_margin+"px"});
    var waveformLegendContext = waveformLegend.get()[0].getContext("2d");
    waveformLegendContext.font = "10px Arial";
    waveformLegendContext.canvas.width=waveformLegend.width();
    waveformLegendContext.canvas.height=waveformLegend.height();
    waveformLegendContext.clearRect(0, 0, waveformLegend.width(), waveformLegend.height());
    var legend_middle=parseFloat($("#waveform").width()) <= 550 ? left_margin/2 : left_margin*3/5;//this weird math is just what I think looks good (pixel perfect magic...)
    waveformLegendContext.strokeText("1",legend_middle,10);
    waveformLegendContext.strokeText("0",legend_middle,waveformLegend.height()/2+3); // 0 has height of 6px give or take - hence 6/2 == 3
    waveformLegendContext.strokeText("-1",legend_middle-3,waveformLegend.height()-10/2);
}
function initTimeline(){
    /*
    Android browser can't get duration right until music starts playing...
    This function is called for the first time when web page loads, and the second time when music starts playing.
     */
    if(timelineInitialized<=2){
        var audio_duration=parseFloat(audio.duration);
        if(audio_duration<=0 || isNaN(audio_duration)) return;
        wavesurfer.backend.getDuration=function(){return audio_duration;};

        var timeline = Object.create(WaveSurfer.Timeline);

        timeline.init({
          wavesurfer: wavesurfer,
          container: '#waveform-timeline'
        });
        timelineInitialized++;
        wavesurfer.drawBuffer();
        drawWaveformLegend();
    }
}
function reposition_waveform(){
    /*
    We want to keep the start and the end of the waveform precisely in sync with the start and the end of the spectrogram.
     */
    var spectrogram_width=SPECTROGRAM_IMG.width();
    var left_margin=LEFT_IMG_MARGIN*spectrogram_width/SPECTROGRAM_IMAGE_WIDTH;
    var right_margin=RIGHT_IMG_MARGIN*spectrogram_width/SPECTROGRAM_IMAGE_WIDTH;
    var default_padding=parseFloat($(".content").css("padding"))  || 15 ; //idk why but $(".content").css("padding") doesn't work in firefox
    $("#waveform-row").css({"margin-left":left_margin-default_padding+"px","margin-right":right_margin-default_padding+"px"});
    wavesurfer.drawBuffer();
    var audio_progress_percentage=audio.currentTime/audio.duration;
    wavesurfer.drawer.progress(audio_progress_percentage);
}
function updateWaveform(){
    /*
        window resize callback - updates stuff to look good
    */
    init_spectrogram_cursor();
    updateSpectrogramCursor();
    $("#violin-photo").height(Math.max($("#description").height()+$("#spectrum_chart").height(),150));
    reposition_waveform();
    drawWaveformLegend();
}
function draw_spectrum_for_whole_audio_track(){
    spectrum_canvas_context.clearRect(0, 0, 550, 250);
    drawSpectrum(spectrum_for_whole_audio_track);
}
function create_audio_element(){
    /*
    Creates audio with wav as main source and mp3 as fallback for browsers that do not support wav (IE).
     */
    audio= new Audio();
    $(audio).append('<source id="wavSource" type="audio/wav" src="'+WAV_AUDIO_LINK+'" />');
    audio.controls = true;
    audio.autoplay = false;
    audio.onloadedmetadata=initTimeline; //http://stackoverflow.com/a/11205198
    $(audio).width("100%");
    $("#audio_player").append(audio);
    //TODO only if fallback_audio!=undef
    $(audio).append('<source id="mp3Source" type="audio/mp3" src="'+MP3_AUDIO_LINK+'" />');


    $(audio).bind("timeupdate", onAudioUpdate);
    //timeupdate is fired too slowly, we want to update the charts every 50ms for user to have a smooth feeling
    $(audio).bind("play", function(){
        audio_clock = setInterval(
            function(){
                onAudioUpdate();
            },
            50
        );
    });
    $(audio).bind("pause", function(){
        clearInterval(audio_clock);
    });

    $(audio).bind("ended", function(){
          draw_spectrum_for_whole_audio_track();
          updateSpectrogramCursor();
    });
}
function onAudioUpdate() {
    initTimeline();//for mobile - apparently onloadedmetadata doesn't work
    updateSpectrogramCursor();
    if(audio.currentTime==0 || audio.currentTime==audio.duration){
        draw_spectrum_for_whole_audio_track();
    }
    else if(analyser!=null && typeof analyser!="undefined"){//audio is playing - we only want to draw the live spectrum if the browser supports it
        var array =  new Float32Array(analyser.frequencyBinCount);
        analyser.getFloatFrequencyData(array);
        if(browserSupportsAudioApiAnalyserNode || getMaxOfArray(array)+Math.abs(analyser.minDecibels)>0){
            browserSupportsAudioApiAnalyserNode=true;
            spectrum_canvas_context.clearRect(0, 0, 550, 250);
            drawSpectrum(array);
        }
    }
}

function updateSpectrogramCursor(){
    var spectrogram_width=SPECTROGRAM_IMG.width();
    var left_margin=parseFloat(LEFT_IMG_MARGIN)*spectrogram_width/SPECTROGRAM_IMAGE_WIDTH;
    var right_margin=parseFloat(RIGHT_IMG_MARGIN)*spectrogram_width/SPECTROGRAM_IMAGE_WIDTH;
    var audio_progress_percentage=audio.currentTime/audio.duration;
    if(isNaN(audio_progress_percentage)) audio_progress_percentage=0;
    wavesurfer.drawer.progress(audio_progress_percentage);
    if(audio_progress_percentage==0 || audio_progress_percentage==1){
        SPECTROGRAM_CURSOR.width(0).css("border-right-width","0px");
    }
    else{
        SPECTROGRAM_CURSOR.width(left_margin+audio_progress_percentage*(spectrogram_width-left_margin-right_margin)-1).css("border-right-width","2px");
    }
}
function init_spectrogram_cursor(){
    var spectrogram_height=SPECTROGRAM_IMG.height();
    var top_margin=parseFloat(TOP_IMG_MARGIN)*spectrogram_height/SPECTROGRAM_IMAGE_HEIGHT;
    var bottom_margin=parseFloat(BOTTOM_IMG_MARGIN)*spectrogram_height/SPECTROGRAM_IMAGE_HEIGHT;
    SPECTROGRAM_CURSOR.css("top",top_margin+"px");
    SPECTROGRAM_CURSOR.css("height",Math.floor(spectrogram_height-top_margin-bottom_margin+1)+"px");
}

function drawSpectrum(array) {
    /*
    maybe try this: http://www.flotcharts.org/flot/examples/image/index.html
    to get to work next time instead of writing all this code
     */
    if(array==undefined) return;

    var left_margin=35;
    var bottom_margin=50;
    var y_axis_height=200;
    var min_dB_value=-100;

    spectrum_canvas_context.fillStyle=gradient;
    for ( var i = 0; i < (array.length); i++ ){
        var value = array[i];
        var strip_height=(y_axis_height/Math.abs(min_dB_value))*Math.max(Math.abs(min_dB_value)+Math.min(value,0),0);
        spectrum_canvas_context.fillRect(i+left_margin,y_axis_height-strip_height,1,strip_height);
    }

    //draw legend for x and y axis
    spectrum_canvas_context.font = "10px Arial";
    //y axis
    spectrum_canvas_context.strokeText("0dB",0,10);
    spectrum_canvas_context.strokeText("-50dB",0,y_axis_height/2);
    spectrum_canvas_context.strokeText("-100dB",0,y_axis_height);

    //x axis
    var text_to_X_axis_padding=15;
    //TODO for loop for values [0,10,20]...
    spectrum_canvas_context.strokeText("0Hz",left_margin,y_axis_height+text_to_X_axis_padding);
    //22 because the y axis goes up to 22kHZ
    spectrum_canvas_context.strokeText("10kHz",left_margin+((SPECTRUM_FFT_SIZE/2)*10/22),y_axis_height+text_to_X_axis_padding);
    spectrum_canvas_context.strokeText("20kHz",left_margin+((SPECTRUM_FFT_SIZE/2)*20/22),y_axis_height+text_to_X_axis_padding);


    //draw x and y axis
    var axis_thickness=1;//in pixels
    spectrum_canvas_context.fillStyle="black";
    spectrum_canvas_context.fillRect(left_margin-axis_thickness,y_axis_height,SPECTRUM_FFT_SIZE/2+axis_thickness,axis_thickness);//x axis
    spectrum_canvas_context.fillRect(left_margin-axis_thickness,0,axis_thickness,y_axis_height);//y axis
}


$().ready(function(){
    set_up_enquire();
    spectrum_canvas_context = $("#canvas").get()[0].getContext("2d");
    create_gradient();
    wavesurfer= WaveSurfer.create({
        container: '#waveform',
        waveColor: 'red',
        progressColor: 'purple',
        autoCenter: true
    });
    //unregister onclicked event - user is going to control the audio playback using the <audio> element instead
    wavesurfer.drawer.handlers.click[0]=function(e){};

    SPECTROGRAM_IMG=$("#spectogram");
    SPECTROGRAM_CURSOR=$("#spectogramTimeStamp");

    //minimum violin-photo height = 150
    //maximum violin-photo height max( the description of the violin height, 150)
    $("#violin-photo").height(Math.max($("#description").height()+$("#spectrum_chart").height(),150));

    $.getJSON(WAVEFORM_LINK,function(data){
        //TODO split this to 2 framgents - one for waveform and the other one for spectrum
        wavesurfer.backend.getPeaks=function(){return data.waveformjs};

        $.getJSON(SPECTRUM_LINK,function(data){
            spectrum_for_whole_audio_track=data;
            drawSpectrum(spectrum_for_whole_audio_track);
        });
        try{
            context= new (window.AudioContext||window.webkitAudioContext||window.mozAudioContext||window.oAudioContext||window.msAudioContext)();
            analyser= context.createAnalyser();
            analyser.fftSize=SPECTRUM_FFT_SIZE;
            analyser.maxDecibels=0;
        }
        catch(err){
            console.log(err);
        }
        onAudioUpdate();
        init_spectrogram_cursor();
        $("#spectogram").bind("load",init_spectrogram_cursor);
        updateSpectrogramCursor();
        reposition_waveform();
        drawWaveformLegend();
        $(window).resize( updateWaveform );
    });
    create_audio_element();

    //Wait for window.onload to fire. See crbug.com/112368 - createMediaElementSource works only after window.onload.
    window.addEventListener('load', function(e) {
      // Our <audio> element will be the audio source.
      if(context!=null && (typeof context)!="undefined"){
          var source = context.createMediaElementSource(audio);
          source.connect(analyser);
          analyser.connect(context.destination);

          // ...call requestAnimationFrame() and render the analyser's output to canvas.
      }
    }, false);
});
