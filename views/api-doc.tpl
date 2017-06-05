<meta charset="utf-8">
<title>Extension REST API Documentation</title>
<style type="text/css">
    body { font-family: Verdana, sans-serif; }
    .content { width: 800px; margin: 0 auto; }
    table { width: 100%; }
    table th, table td {
        padding: 10px;
        vertical-align: top;
    }
    .endpoint { position: relative; }
    .endpoint, .code { font-family: monospace; }
    .desc:first-line { font-weight: bold; }
    .endpoint.auth-required:before {
        content: '✦';
        display: inline-block;
        position: absolute;
        top: 4px;
        right: 5px;
        font-weight: bold;
        font-size: 20px;
        color: #4d4d4d;
    }
</style>

<div class="content">
    <table>
        <tr style="background-color:#CCCFDF"><th colspan="2">API Documentation</th></tr>
        <tr style="background-color:#CCCFDF"><th>ENDPOINT</th><th>DESCRIPTION</th></tr>
         % for color,resource in zip(colors,routes) :
            % docx = (resource.callback.__doc__ or '').strip().replace("\n","<br/>")
            % auth_required = hasattr(resource.callback, 'auth_required')
            <tr style="background-color:{{ color }}">
                <td class="endpoint {{ 'auth-required' if auth_required else '' }}">
                    <pre>{{ resource.method.ljust(6) }} {{ resource.rule }}</pre>
                </td>
                <td class="desc">
                    {{! docx }}
                </td>
            </tr>
         % end
    </table>
    <br>
    <p>
        ✦ Authorization header required (<code>Authorization:Bearer &lt;token&gt;</code>)
    </p>

</div>
