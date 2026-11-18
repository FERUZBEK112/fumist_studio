package uz.fumist.studio;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.*;
import android.widget.Toast;
import androidx.webkit.WebViewCompat;
import androidx.webkit.WebViewFeature;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import org.json.JSONObject;

public final class Studio extends Activity {
    private static final String HOST = "fumist-studio-production.up.railway.app";
    private static final String ORIGIN = "https://" + HOST;
    private static final String EDITOR = ORIGIN + "/mobile-releases/1.3.2/index.html";
    private WebView web;
    private ValueCallback<Uri[]> chooser;
    private String pendingURL, pendingText;

    private boolean internal(Uri uri) {
        return "https".equals(uri.getScheme()) && HOST.equals(uri.getHost()) && (uri.getPort() == -1 || uri.getPort() == 443);
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        web = new WebView(this);
        setContentView(web);
        web.setFitsSystemWindows(true);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (chooser != null) chooser.onReceiveValue(null);
                chooser = callback;
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*");
                intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE);
                try { startActivityForResult(intent, 1); }
                catch (android.content.ActivityNotFoundException e) { chooser.onReceiveValue(null); chooser = null; }
                return true;
            }
        });
        if (WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            WebViewCompat.addWebMessageListener(web, "fumistExport", Collections.singleton(ORIGIN),
                (view, message, origin, topFrame, reply) -> {
                    if (!topFrame) return;
                    try {
                        JSONObject data = new JSONObject(message.getData());
                        String name = data.getString("name");
                        if (!name.equals("FUMIST-project.json") && !name.equals("FUMIST-captions.srt")) return;
                        save(name, "text/plain", null, data.getString("text"));
                    } catch (Exception e) { notice("Faylni saqlab bo‘lmadi"); }
                });
        }
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {
                Uri uri = Uri.parse(url);
                if (internal(uri)) return false;
                if ("https".equals(uri.getScheme()) || "tg".equals(uri.getScheme())) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
                    catch (android.content.ActivityNotFoundException e) { notice("Havolani ochib bo‘lmadi"); }
                }
                return true;
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError error) {
                if (req.isForMainFrame() && !isFinishing()) new AlertDialog.Builder(Studio.this)
                    .setMessage("Internet aloqasini tekshiring").setPositiveButton("Qayta ochish",(d,w)->web.loadUrl(EDITOR)).show();
            }
            @Override public void onPageFinished(WebView view, String url) {
                if (!internal(Uri.parse(url))) return;
                view.evaluateJavascript("(function(){if(!window.fumistExport||window.fumistHook)return;window.fumistHook=true;const click=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){if(this.download&&this.href.startsWith('blob:')){const name=this.download;fetch(this.href).then(r=>r.text()).then(text=>fumistExport.postMessage(JSON.stringify({name,text})));}else click.call(this);};})()",null);
            }
        });
        web.setDownloadListener((url, agent, disposition, mime, size) -> {
            Uri uri = Uri.parse(url);
            if (internal(uri) && uri.getPath().startsWith("/api/download/"))
                save("FUMIST-" + uri.getLastPathSegment() + ".mp4", "video/mp4", url, null);
        });
        if (state == null || web.restoreState(state) == null) web.loadUrl(EDITOR);
    }
    private void notice(String message) { Toast.makeText(this,message,Toast.LENGTH_LONG).show(); }
    private void save(String name,String mime,String url,String content) {
        pendingURL = url;
        pendingText = content;
        startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
            .setType(mime).putExtra(Intent.EXTRA_TITLE,name),2);
    }
    @Override protected void onActivityResult(int code,int result,Intent data) {
        super.onActivityResult(code,result,data);
        if (code == 1 && chooser != null) {
            Uri[] files = null;
            if (result == RESULT_OK && data != null && data.getClipData() != null) {
                files = new Uri[data.getClipData().getItemCount()];
                for (int i=0;i<files.length;i++) files[i]=data.getClipData().getItemAt(i).getUri();
            } else files = WebChromeClient.FileChooserParams.parseResult(result,data);
            chooser.onReceiveValue(files); chooser = null;
        }
        if (code != 2) return;
        final String url = pendingURL, content = pendingText;
        pendingURL = pendingText = null;
        if (result != RESULT_OK || data == null || data.getData() == null) return;
        final Uri dest = data.getData();
        final String cookie = url == null ? null : CookieManager.getInstance().getCookie(url);
        new Thread(() -> {
            HttpURLConnection conn = null;
            try (OutputStream out=getContentResolver().openOutputStream(dest)) {
                if (url == null) out.write(content.getBytes(StandardCharsets.UTF_8));
                else {
                    conn=(HttpURLConnection)new URL(url).openConnection();
                    conn.setInstanceFollowRedirects(false);
                    conn.setConnectTimeout(15000); conn.setReadTimeout(60000);
                    if(cookie!=null) conn.setRequestProperty("Cookie",cookie);
                    if(conn.getResponseCode()!=200) throw new IOException("Download failed");
                    try(InputStream in=conn.getInputStream()) {
                        byte[] buf=new byte[65536]; int n;
                        while((n=in.read(buf))!=-1) out.write(buf,0,n);
                    }
                }
            } catch(Exception e) { runOnUiThread(()->notice("Faylni saqlab bo‘lmadi")); }
            finally { if(conn!=null) conn.disconnect(); }
        }).start();
    }
    @Override protected void onSaveInstanceState(Bundle state) { super.onSaveInstanceState(state); web.saveState(state); }
    @Override public void onBackPressed() { if(web.canGoBack()) web.goBack(); else super.onBackPressed(); }
}
