<meta charset="utf-8">
<title>Extension REST API Documentation</title>
<style type="text/css">
    table th, table td {
        padding: 10px;
    }
    .endpoint {
        font-family: monospace;
    }
</style>

<table>
    <tr style="background-color:#CCCFDF"><th colspan="2">API Documentation</th></tr>
    <tr style="background-color:#CCCFDF"><th>ENDPOINT</th><th>DESCRIPTION</th></tr>
     % for color,resource in zip(colors,routes) :
        % docx = (resource.callback.__doc__ or '').replace("\n","<br/>")
        <tr style="background-color:{{ color }}">
           <td class="endpoint">{{ resource.method }} {{ resource.rule }}</td>
           <td> {{! docx }} </td>
        </tr>
     % end
</table>
