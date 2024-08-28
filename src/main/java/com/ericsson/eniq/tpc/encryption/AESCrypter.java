/*------------------------------------------------------------------------------
 *******************************************************************************
 * COPYRIGHT Ericsson 2012
 *
 * The copyright to the computer program(s) herein is the property of
 * Ericsson Inc. The programs may be used and/or copied only with written
 * permission from Ericsson Inc. or in accordance with the terms and
 * conditions stipulated in the agreement/contract under which the
 * program(s) have been supplied.
 *******************************************************************************
 *----------------------------------------------------------------------------*/

package com.ericsson.eniq.tpc.encryption;

import java.io.InputStream;
import java.io.OutputStream;
import java.security.Key;

import javax.crypto.Cipher;
import javax.crypto.CipherInputStream;
import javax.crypto.CipherOutputStream;
import javax.crypto.spec.SecretKeySpec;

/**
 * This class is used to encrypt and decrypt the file.
 */
public class AESCrypter {

	private final static String cipherName = "AES";
	private final String cipherMethod = "/ECB/PKCS5Padding";

	public AESCrypter() {
	}

	public Key encrypt(InputStream is, OutputStream os) throws Exception {
		CipherOutputStream cos = null;
		Key key = getRandomKey();
		try {
			Cipher cipher = Cipher.getInstance((new StringBuilder())
					.append(cipherName).append(cipherMethod).toString());
			cipher.init(1, key);
			cos = new CipherOutputStream(os, cipher);
			int in;
			while ((in = is.read()) != -1) {
				cos.write(in);
			}
			cos.close();
		} catch (Exception e) {
			throw new Exception((new StringBuilder())
					.append("Encryption failed: ").append(e.getMessage())
					.toString());
		}
		return key;
	}

	public void decrypt(InputStream is, OutputStream os, Key key)
			throws Exception {
		try {
			Cipher cipher = Cipher.getInstance((new StringBuilder())
					.append(cipherName).append(cipherMethod).toString());
			cipher.init(2, key);
			CipherInputStream cis = new CipherInputStream(is, cipher);
			int in;
			while ((in = cis.read()) != -1)
				os.write(in);
		} catch (Exception e) {
			throw new Exception((new StringBuilder())
					.append("Decryption failed: ").append(e.getMessage())
					.toString());
		}
	}

	public static Key getRandomKey() {
		return new SecretKeySpec(getRandomBytes(16), cipherName);
	}

	private static byte[] getRandomBytes(int num) {
		if (num > 0) {
			byte bytes[] = new byte[num];
			for (int i = 0; i < bytes.length; i++)
				bytes[i] = (byte) (int) Math.round(Math.random() * 127D);

			return bytes;
		} else {
			return null;
		}
	}
}
