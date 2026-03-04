'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Subscription {
  plan: string;
  status: string;
  current_period_start: string;
  current_period_end: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
}

interface PlanDetails {
  name: string;
  price: string;
  color: string;
}

export default function SubscriptionSettingsPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchSubscription();
  }, []);

  const fetchSubscription = async () => {
    try {
      const res = await fetch('/api/billing/subscription');
      const data = await res.json();
      setSubscription(data);
    } catch (error) {
      console.error('Failed to fetch subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Are you sure? You\'ll keep access until the end of your billing period.')) {
      return;
    }
    
    setActionLoading(true);
    try {
      const res = await fetch('/api/billing/cancel-subscription', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (res.ok) {
        setMessage('Subscription will cancel at the end of this billing period.');
        fetchSubscription();
      } else {
        const error = await res.json();
        setMessage(error.detail || 'Failed to cancel subscription');
      }
    } catch (error) {
      setMessage('Network error. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReactivate = async () => {
    setActionLoading(true);
    try {
      const res = await fetch('/api/billing/reactivate-subscription', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (res.ok) {
        setMessage('Subscription reactivated successfully!');
        fetchSubscription();
      } else {
        const error = await res.json();
        setMessage(error.detail || 'Failed to reactivate subscription');
      }
    } catch (error) {
      setMessage('Network error. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const openCustomerPortal = async () => {
    try {
      const res = await fetch('/api/billing/portal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (res.ok) {
        const { url } = await res.json();
        window.location.href = url;
      }
    } catch (error) {
      setMessage('Failed to open billing portal');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const planDetails: Record<string, PlanDetails> = {
    spark: { name: 'Spark', price: 'Free', color: 'bg-gray-100 text-gray-800' },
    forge: { name: 'The Forge', price: '$4.99/month', color: 'bg-indigo-100 text-indigo-800' },
    identity: { name: 'The Identity', price: '$10.99/month', color: 'bg-purple-100 text-purple-800' }
  };

  // Safe lookup with fallback to spark
  const currentPlan = subscription?.plan 
    ? planDetails[subscription.plan] || planDetails.spark 
    : planDetails.spark;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Subscription</h1>

      {message && (
        <div className={`mb-6 p-4 rounded-lg ${message.includes('success') || message.includes('reactivated') ? 'bg-green-50 text-green-700' : 'bg-blue-50 text-blue-700'}`}>
          {message}
        </div>
      )}

      {/* Current Plan Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Current Plan</h2>
            <p className="text-sm text-gray-500">Manage your subscription and billing</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${currentPlan.color}`}>
            {currentPlan.name}
          </span>
        </div>

        <div className="border-t border-gray-200 pt-4">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-500">Price</p>
              <p className="font-medium text-gray-900">{currentPlan.price}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <p className="font-medium capitalize text-gray-900">{subscription?.status || 'Unknown'}</p>
            </div>
          </div>

          {subscription?.current_period_end && subscription.plan !== 'spark' && (
            <div className="mb-4">
              <p className="text-sm text-gray-500">
                {subscription.status === 'canceling' 
                  ? 'Access until' 
                  : 'Next billing date'}
              </p>
              <p className="font-medium text-gray-900">
                {new Date(subscription.current_period_end).toLocaleDateString('en-US', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric'
                })}
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 mt-6">
          {subscription?.plan === 'spark' ? (
            <Link
              href="/settings/upgrade"
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
            >
              Upgrade Plan
            </Link>
          ) : (
            <>
              <button
                onClick={openCustomerPortal}
                className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                Manage Billing
              </button>

              {subscription?.status === 'active' ? (
                <button
                  onClick={handleCancel}
                  disabled={actionLoading}
                  className="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
                >
                  {actionLoading ? 'Processing...' : 'Cancel Subscription'}
                </button>
              ) : subscription?.status === 'canceling' ? (
                <button
                  onClick={handleReactivate}
                  disabled={actionLoading}
                  className="bg-green-50 text-green-600 border border-green-200 px-4 py-2 rounded-lg font-medium hover:bg-green-100 transition-colors disabled:opacity-50"
                >
                  {actionLoading ? 'Processing...' : 'Reactivate Subscription'}
                </button>
              ) : null}
            </>
          )}
        </div>
      </div>

      {/* Plan Comparison */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Plans</h3>
        <div className="grid md:grid-cols-3 gap-4">
          {Object.entries(planDetails).map(([key, plan]) => (
            <div
              key={key}
              className={`bg-white rounded-lg p-4 border-2 ${
                subscription?.plan === key ? 'border-indigo-500' : 'border-transparent'
              }`}
            >
              <h4 className="font-semibold text-gray-900">{plan.name}</h4>
              <p className="text-2xl font-bold text-gray-900 mt-2">{plan.price}</p>
              {subscription?.plan === key && (
                <span className="inline-block mt-2 text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                  Current Plan
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}