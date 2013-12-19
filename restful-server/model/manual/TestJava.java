import java.util.Scanner;
import java.net.*;
import java.io.*;

public class TestJava {
    public static void main(String[] args) throws Exception {
        TestJava testObj = new TestJava();
        testObj.versionInfo();
        testObj.authUser();
        testObj.handleHttp();
    }

    TestJava() {
        this.m_userName = "";
        this.m_password = "";
        this.m_url = "http://127.0.0.1:88";
    }

    public void versionInfo() {
        System.out.println("");
        System.out.println(" ==========================================================");
        System.out.println("           RESTful API test program for JAVA");
        System.out.println("            Developer : develop-3@vmediax.com");
        System.out.println("                 Date : 2013-05");
        System.out.println("              ^__^ Good Luck ^__^");
        System.out.println(" ==========================================================");
        System.out.println("");
    }

    public void authUser() {
        System.out.println("");
        System.out.println(" Ok, Let's GO !");
        System.out.println(" Now, Authentication ===>");
        while (true) {
            Scanner input = new Scanner(System.in);

            System.out.print("         User Name: ");
            String name = input.nextLine();
            System.out.print("     User Password: ");
            String password = input.nextLine();

            String method = "post";
            String url = this.m_url + "/auth";
            String params = "{\"name\":\"" + name + "\",\"passwd\":\"" + password+ "\"}";  // json format
            String header = "";
            ResposeHttp ret = httpRequest(method, url, params, header);
            if (ret.status == 200) {
                System.out.println("");
                System.out.println(" Congratulations, Authentication Success ^__^");
                this.m_userName = name;
                this.m_password = password;
                break;
            }
            else {
                System.out.println("");
                System.out.println(" Oh, Authentication Failed @ _ @, maybe you are not lucky...");
                System.out.println("");
                System.out.println(" Pls Authentication Again ===>");
            }
        }
    }

    public ResposeHttp httpRequest(String method, String url, String params, String header) {
        URL urlObj = null;
        HttpURLConnection conn = null;
        ResposeHttp respose = new ResposeHttp();

        try {
            urlObj = new URL(url);
        }
        catch (MalformedURLException e){
            // System.out.println("here 1");
            return respose;
        }

        try {
            conn = (HttpURLConnection) urlObj.openConnection();
        }
        catch (IOException e) {
            // System.out.println("here 2");
            return respose;
        }

        try {
            conn.setRequestMethod(method.toUpperCase());
            conn.setDoInput(true);
            conn.setDoOutput(true);
        }
        catch (ProtocolException e) {
            // System.out.println("here 3");
            return respose;
        }

        try {
            if (! header.isEmpty()) {
                // set http request header info
                // set cookie
                conn.setRequestProperty("Cookie", header);
            }
            if (method.toUpperCase() == "POST") {
                conn.setUseCaches(false);
            }

            // connect to the http request url
            conn.connect();

            if (! params.isEmpty()) {
                OutputStreamWriter out = new OutputStreamWriter(conn.getOutputStream());
                out.write(params);
                out.flush();
                out.close();
            }

            String result = "";
            try {
                BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                result = in.readLine();
                in.close();
            }
            catch (IOException e) {
                // System.out.println("here 5");
                respose.status = conn.getResponseCode();
                respose.reason = conn.getResponseMessage();
                return respose;
            }

            // set return class var
            respose.body = result;
            respose.status = conn.getResponseCode();
            respose.reason = conn.getResponseMessage();

            conn.disconnect();
        }
        catch (IOException e) {
            // System.out.println("here 4");
            return respose;
        }

        return respose;
    }

    public void handleHttp() {
        while (true) {
            String method = "get";
            String url = "";
            String params = "";
            // the header info is 'Cookie'
            String header = "user_name=" + this.m_userName + ";user_passwd=" + this.m_password + ";";

            Scanner input = new Scanner(System.in);
            System.out.println("");
            System.out.println(" Pls input http request infomation:");

            System.out.print("      Method [get, post, put, delete] (get): ");
            String methodTmp = input.nextLine();
            if (! methodTmp.isEmpty()) {
                while (true) {
                    if (methodTmp.equals("get") || methodTmp.equals("post") || methodTmp.equals("put") || methodTmp.equals("delete")) {
                        method = methodTmp;
                        break;
                    }
                    else {
                        System.out.print(" Http method wrong, Pls input again: ");
                        methodTmp = input.nextLine();
                    }
                }
            }

            System.out.print("      URL: ");
            url = input.nextLine();
            System.out.print("      Data: ");
            params = input.nextLine();
            url = this.m_url + url;

            ResposeHttp ret = httpRequest(method, url, params, header);
            this.echo(ret);
        }
    }

    public void echo(ResposeHttp res) {
        System.out.println("");
        System.out.println(" Respose Result");
        System.out.println(" ==================================================================");
        System.out.println("      status : " + res.status);
        System.out.println("      reason : " + res.reason);
        System.out.println("        body : " + res.body);
        System.out.println(" ==================================================================");
        System.out.println("");
    }

    public String m_userName;
    public String m_password;
    public String m_url;

    public class ResposeHttp {
        ResposeHttp() {
            status = 0;
            reason = "";
            body = "";
        }
        public int status;
        public String reason;
        public String body;
    }
}
