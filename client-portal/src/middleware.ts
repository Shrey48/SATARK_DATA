import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

/**
 * Sanitizer — strips dangerous characters from user input.
 * Produces E_sanitize edges when called before downstream operations.
 */
export function sanitizePortfolioId(raw: string): string {
  if (!raw) throw new Error('empty input');
  const clean = raw.replace(/['";<>{}|\\]/g, '').trim().slice(0, 64);
  if (!/^[A-Za-z0-9\-_]+$/.test(clean)) throw new Error('invalid portfolio id');
  return clean;
}

/**
 * Auth middleware — verifyToken.
 * BUG D TEST: Routes using this middleware should get declared_restrictive.
 * Currently posture engine ignores middleware and marks routes permissive.
 */
export function verifyToken(req: Request, res: Response, next: NextFunction): void {
  const auth = req.headers.authorization;
  if (!auth?.startsWith('Bearer ')) {
    res.status(401).json({ error: 'missing token' });
    return;
  }
  try {
    const payload = jwt.verify(auth.slice(7), process.env.JWT_SECRET || 'secret');
    (req as any).user = payload;
    next();
  } catch {
    res.status(401).json({ error: 'invalid token' });
  }
}
