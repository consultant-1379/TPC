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

import java.io.*;
import java.math.BigInteger;
import java.security.*;
import java.security.spec.*;
import java.util.Enumeration;
import java.util.zip.*;
import javax.crypto.*;
import javax.crypto.spec.SecretKeySpec;

/**
 * This class is used as a delegate to encrypt the file.
 */
public class ZipCrypter {
	
	public static String testString = "This is a small test string to check that the encryption works!";
	public static final String DEFAULT_CIPHER = "RSA/ECB/PKCS1Padding";
	public static final String DEFAULT_CIPHER_NAME = "RSA";
	public static final BigInteger DEFAULT_KEY_MOD = new BigInteger(
			"123355219375882378192369770441285939191353866566017497282747046709534536708757928527167390021388683110840288891057176815668475724440731714035455547579744783774075008195670576737607241438665521837871490309744873315551646300131908174140715653425601662203921855253249615512397376967139410627761058910648132466577");
	public static final BigInteger DEFAULT_KEY_EXP = new BigInteger("65537");
	protected int cryptMode;
	protected File fileTarget;
	protected BigInteger keyMod;
	protected BigInteger keyExp;
	protected boolean isPublic;
	protected Key rsaKey;
	
	public class ZipCrypterDataEntry {

		public byte[] getData() {
			return data;
		}

		public void setData(byte data[]) {
			this.data = data;
		}

		public byte[] getExtra() {
			return extra;
		}

		public void setExtra(byte extra[]) {
			this.extra = extra;
		}

		public int getSize() {
			return data.length;
		}

		private byte data[];
		private byte extra[];
		final ZipCrypter this$0;

		public ZipCrypterDataEntry() {
			super();
			this$0 = ZipCrypter.this;
		}
	}

	public ZipCrypter() {
		cryptMode = 2;
		fileTarget = null;
		keyMod = null;
		keyExp = null;
		isPublic = true;
		rsaKey = null;
	}

	public void execute() throws Exception {

		initKey();
		if (fileTarget == null)
			throw new Exception("The target file has not been specified.");
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		ZipOutputStream zos = new ZipOutputStream(bos);
		zos.setMethod(8);

		try {
			ZipFile zf = new ZipFile(fileTarget);
			Enumeration entries = zf.entries();
			do {
				if (!entries.hasMoreElements())
					break;
				ZipEntry ze = (ZipEntry) entries.nextElement();
				if (!ze.isDirectory()) {
					long startTime = System.currentTimeMillis();
					ZipEntry newEntry = new ZipEntry(ze.getName());
					ZipCrypterDataEntry output = cryptInputStream(
							zf.getInputStream(ze), cryptMode, ze.getExtra(),
							rsaKey);
					newEntry.setSize(output.getSize());
					newEntry.setExtra(output.getExtra());
					newEntry.setTime(ze.getTime());
					CRC32 crc = new CRC32();
					crc.update(output.getData());
					newEntry.setCrc(crc.getValue());

					zos.putNextEntry(newEntry);
					zos.write(output.getData());
					zos.closeEntry();
					double totalTime = (double) (System.currentTimeMillis() - startTime) / 1000D;
				}
			} while (true);
			zf.close();
			zos.flush();
			zos.close();
			if (!fileTarget.exists() || fileTarget.canWrite())
				try {
					OutputStream outStream = new FileOutputStream(fileTarget);
					bos.flush();
					outStream.write(bos.toByteArray());
					outStream.flush();
					outStream.close();
					bos.close();
				} catch (FileNotFoundException e) {
					throw new Exception("Could not find the file.");
				}
		} catch (Exception e) {
			throw new Exception(e.getMessage(), e);
		}
	}

	protected ZipCrypterDataEntry cryptInputStream(InputStream is, int mode,
			byte extra[], Key key) throws Exception {
		ZipCrypterDataEntry returnEntry = new ZipCrypterDataEntry();
		AESCrypter aes = new AESCrypter();
		ByteArrayOutputStream entryBos = new ByteArrayOutputStream();
		Key aesKey = null;
		if (mode == 2) {
			try {
				aesKey = decryptAESKey(extra, key);
				int in;
				if (aesKey == null)
					while ((in = is.read()) != -1)
						entryBos.write(in);
				else
					aes.decrypt(is, entryBos, aesKey);
			} catch (Exception e) {
				throw new Exception(e.getMessage(), e);
			}
		} else {
			aesKey = aes.encrypt(is, entryBos);
			if (aesKey == null) {
				throw new Exception("AES Key generation failed!");
			}
			try {
				returnEntry.setExtra(encryptAESKey(key, aesKey));
			} catch (Exception e) {
				throw new Exception(e.getMessage(), e);
			}
		}
		returnEntry.setData(entryBos.toByteArray());
		return returnEntry;
	}

	protected byte[] encryptAESKey(Key rsaKey2, Key aesKey)
			throws NoSuchAlgorithmException, NoSuchPaddingException,
			InvalidKeyException, IllegalBlockSizeException, BadPaddingException {
		Cipher cipher = Cipher.getInstance(DEFAULT_CIPHER);
		cipher.init(1, rsaKey2);
		byte key[] = aesKey.getEncoded();
		return cipher.doFinal(key);
	}

	public Key decryptAESKey(byte encrypted[], Key rsaKey2) throws Exception {
		if (encrypted == null || encrypted.length == 0)
			return null;
		Cipher cipher = Cipher.getInstance(DEFAULT_CIPHER);
		cipher.init(2, rsaKey2);
		byte key[];
		try {
			key = cipher.doFinal(encrypted);
		} catch (Exception e) {
			e.printStackTrace();
			return null;
		}
		return new SecretKeySpec(key, "AES");
	}

	protected void initKey() throws Exception {
		if (keyMod == null || keyExp == null) {
			keyMod = DEFAULT_KEY_MOD;
			keyExp = DEFAULT_KEY_EXP;
		}
		if (isPublic)
			rsaKey = getPublicKey(keyMod, keyExp);
		else
			rsaKey = getPrivateKey(keyMod, keyExp);
	}

	public static boolean isValidKeyPair(PublicKey pubKey, PrivateKey privKey) {
		try {
			Cipher encrypter = Cipher.getInstance(DEFAULT_CIPHER);
			encrypter.init(1, privKey);
			Cipher decrypter = Cipher.getInstance(DEFAULT_CIPHER);
			decrypter.init(2, pubKey);
			byte encrypted[] = encrypter.doFinal(testString.getBytes());
			byte decrypted[] = decrypter.doFinal(encrypted);
			String result = new String(decrypted);
			return result.equals(testString);
		} catch (Exception e) {
			return false;
		}
	}

	public static PublicKey getPublicKey(BigInteger pubMod, BigInteger pubExp)
			throws Exception {
		try {
			RSAPublicKeySpec keySpec = new RSAPublicKeySpec(pubMod, pubExp);
			KeyFactory keyFactory = KeyFactory.getInstance(DEFAULT_CIPHER_NAME);
			return keyFactory.generatePublic(keySpec);
		} catch (NoSuchAlgorithmException e) {
			e.printStackTrace();
		} catch (InvalidKeySpecException e) {
			throw new Exception("Invalid key specification");
		}
		throw new Exception("Could not initialize the KeyFactory");
	}

	public static PrivateKey getPrivateKey(BigInteger privMod,
			BigInteger privExp) throws Exception {
		try {
			RSAPrivateKeySpec keySpec = new RSAPrivateKeySpec(privMod, privExp);
			KeyFactory keyFactory = KeyFactory.getInstance(DEFAULT_CIPHER_NAME);
			return keyFactory.generatePrivate(keySpec);
		} catch (NoSuchAlgorithmException e) {
			throw new Exception("Could not initialize the KeyFactory");
		} catch (InvalidKeySpecException e) {
			throw new Exception("Invalid key specification");
		}
	}

	public void setKeyModulate(String mod) {
		keyMod = new BigInteger(mod);
	}

	public void setKeyExponent(String exp) {
		keyExp = new BigInteger(exp);
	}

	public void setCryptType(String type) {
		if (type.equalsIgnoreCase("encrypt"))
			cryptMode = 1;
		else
			cryptMode = 2;
	}

	public void setIsPublicKey(String isPublic) {
		this.isPublic = Boolean.parseBoolean(isPublic);
	}

	public void setFile(String file) throws Exception {
		if (file == "")
			fileTarget = null;
		fileTarget = new File(file);
		if (!fileTarget.exists() || !fileTarget.canRead())
			throw new Exception(
					"The target file cannot be accessed or does not exist.");
		else
			return;
	}
}
