/*
testing setup:
yarn add sinon
yarn add qunit-phantomjs-runner
yarn add underscore
npm install -g phantomjs

run tests with:
phantomjs node_modules/qunit-phantomjs-runner/runner.js test.html
or open test.html in your browser
 */
$.ready=function () {};
QUnit.test( "test init_spectrogram_cursor", function( assert ) {
    TOP_IMG_MARGIN=19;
    BOTTOM_IMG_MARGIN=39;
    SPECTROGRAM_IMAGE_HEIGHT=500;
    SPECTROGRAM_IMG=Object();
    SPECTROGRAM_IMG.height=function () {};
    var mock_SPECTROGRAM_IMG_height=sinon.stub(SPECTROGRAM_IMG,"height");
    mock_SPECTROGRAM_IMG_height.returns(287);

    SPECTROGRAM_CURSOR=Object();
    SPECTROGRAM_CURSOR.css=function () {};
    var mock_SPECTROGRAM_CURSOR_css=sinon.stub(SPECTROGRAM_CURSOR,"css");
    var expected_args=[["top","10.906px"],["height","254px"]];
    init_spectrogram_cursor();
    assert.ok( mock_SPECTROGRAM_CURSOR_css.callCount==expected_args.length);
    for(var i = 0; i<expected_args.length;i++)
        assert.ok(_.isEqual(mock_SPECTROGRAM_CURSOR_css.getCalls()[i].args,expected_args[i]));

});
