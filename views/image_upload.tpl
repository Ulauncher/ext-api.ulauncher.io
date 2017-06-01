<meta charset="utf-8">
<title>Image upload</title>

<!--
Source: https://gist.github.com/WebReflection/f04425ce4cfeb18d75236cb50255e4bc
-->

<form
  id="testForm"
  action="/extensions/{{ ext_id }}/images"
  method="post"
  enctype="multipart/form-data"
>
  <p><input type="file" name="file" multiple></p>
  <input type="submit">
</form>

<script type="text/javascript">
document
  .querySelector('#testForm')
  .addEventListener('submit', function processForm(e) {
    e.preventDefault();
    console.log('processForm');

    var form = e.currentTarget;
    var multipleFiles = form.querySelector('input[type=file]');

    // only if there is something to do ...
    if (multipleFiles.files.length) {
      var submit = form.querySelector('[type=submit]');
      var request = new XMLHttpRequest();
      var formData = Array.prototype.reduce.call(
        multipleFiles.files,
        function (formData, file, i) {
          formData.append(multipleFiles.name + i, file);
          return formData;
        },
        new FormData()
      );

      // avoid multiple repeated uploads
      // (histeric clicks on slow connection)
      submit.disabled = true;

      // do the request using form info
      request.open(form.method, form.action);
      // want to distinguish from non-JS submits?
      request.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
      request.setRequestHeader('Authorization', 'Bearer {{ token }}');
      request.send(formData);

      request.onload = function(e) {
        // clean up the form eventually
        console.log('Request Status', request.status);
        // make this form usable again
        submit.disabled = false;
        // enable the submit on abort/error too
        // to make the user able to retry
      };
    }
  });
</script>