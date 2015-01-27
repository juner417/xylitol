import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.*;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FSDataInputStream;
import org.apache.hadoop.fs.FSDataOutputStream;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IOUtils;


public class readWriteAppend {

	/**
	 * @param args
	 */
	
	public void doRead(FileSystem fs, String path) throws IOException {
		Path filePath = new Path(path);
		FSDataInputStream fis = fs.open(filePath);
		
		IOUtils.copyBytes(fis, System.out, 1048576);
		fis.close();
	}
	
	public void doWrite(FileSystem fs, String path) throws IOException, InterruptedException {
		Path filePath = new Path(path);
		FSDataOutputStream fos = fs.create(filePath);
		
		Calendar cal = Calendar.getInstance();
		SimpleDateFormat date = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
		//String dt = date.format(cal.getTime()).toString();
		
		for (int cnt = 1; cnt < 30; cnt++) {
			fos.writeBytes(date.format(cal.getTime()).toString() + " " + cnt + "th write Hello World~");
			fos.write('\n');
			System.out.println("current " + cnt + " th write");
			System.out.println("wait 0.5 sec");
			Thread.sleep(1 * 500);
			
		}
		fos.close();
		
	}
	
	public void doAppend(FileSystem fs, String path) throws IOException, InterruptedException {
		Path filePath = new Path(path);
		FSDataOutputStream fos = fs.append(filePath);
		
		Calendar cal = Calendar.getInstance();
		SimpleDateFormat date = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
		//String dt = date.format(cal.getTime()).toString();
		
		for (int cnt = 1; cnt < 30; cnt++) {
			fos.writeBytes(date.format(cal.getTime()).toString() +" "+ cnt + "th append Hello World~");
			fos.write('\n');
			System.out.println("current " + cnt + " th append");
			System.out.println("wait 0.5 sec");
			Thread.sleep(1 * 500);
			
		}
		fos.close();
		
		
	}
	public static void main(String[] args) throws IOException, InterruptedException {
		// TODO Auto-generated method stub
		
		if (args.length < 3) {
			System.err.println("WARN) Plz check the args");
			System.err.println("USAGE) hadoop jar readWriteAppend hdfspath filepath cmd");
			System.err.println("cmd - read write append");
			System.exit(255);
		}
		String fsPath = args[0];
		String filepath = args[1];
		String cmd = args[2];
		
		System.out.println(fsPath.toString() +", " + filepath.toString() + ", " + cmd.toString() );
		Configuration conf = new Configuration();
		conf.set("fs.default.filename", fsPath);
		FileSystem dfs = FileSystem.get(conf);
		
		readWriteAppend rwa = new readWriteAppend();
		
		if (cmd.equals("write")) {
			rwa.doWrite(dfs, filepath);
		} else if (cmd.equals("append")) {
			rwa.doAppend(dfs, filepath);
		} else if (cmd.equals("read")) {
			rwa.doRead(dfs, filepath);
		} else {
			System.err.println("WARN) Plz check the [CMD] args : " + cmd.toString());
		}

		dfs.close();
	}

}


