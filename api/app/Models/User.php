<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\SoftDeletes;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;
use Illuminate\Support\Facades\Hash;

class User extends Authenticatable
{
    use HasApiTokens, HasUuids, SoftDeletes, Notifiable;

    /**
     * The attributes that are mass assignable.
     *
     * @var array<int, string>
     */
    protected $table = 'core_users';

    protected $fillable = ['id', 'enterprise_id', 'name', 'email', 'password', 'role'];

    protected $hidden = ['password', 'remember_token'];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'password'          => 'hashed',
    ];

    /**
     * Mutator: set the password attribute.
     * If the provided value already looks like a bcrypt hash ($2y$|$2b$|$2a$), store it verbatim
     * to avoid double-hashing when receiving hashes from clients.
     */
    public function setPasswordAttribute($value)
    {
        if (is_string($value) && preg_match('/^\$2[aby]\$.{56}$/', $value)) {
            $this->attributes['password'] = $value;
            return;
        }

        $this->attributes['password'] = Hash::make($value);
    }

    public function enterprise()
    {
        return $this->belongsTo(Entreprise::class, 'enterprise_id');
    }
}
