package uz.fumist.studio;

import android.app.Activity;
import android.os.Bundle;
import android.net.Uri;
import androidx.browser.customtabs.CustomTabsIntent;

public final class Studio extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        new CustomTabsIntent.Builder().setShowTitle(true).build()
            .launchUrl(this, Uri.parse("https://fumist-studio-production.up.railway.app/"));
        finish();
    }
}
